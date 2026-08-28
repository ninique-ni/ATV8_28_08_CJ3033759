import sys
import re
import sqlite3
import requests
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLineEdit, QPushButton, QMessageBox, QLabel, 
    QGroupBox, QFrame
)
from PySide6.QtCore import Qt

ALKIMINS_STYLE = """
QWidget {
    background-color: #1e2124;
    color: #d1d5db;
    font-family: 'Segoe UI', -apple-system, Roboto, sans-serif;
    font-size: 13px;
}

QGroupBox {
    font-weight: 600;
    font-size: 12px;
    border: 1px solid #32363c;
    border-radius: 6px;
    margin-top: 12px;
    padding: 16px 12px 12px 12px;
    background-color: #24272c;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #94a3b8;
}

QLabel {
    color: #9ca3af;
    font-weight: 600;
    font-size: 11px;
}

QLineEdit {
    background-color: #181a1d;
    border: 1px solid #363a40;
    border-radius: 4px;
    padding: 7px 10px;
    color: #e5e7eb;
}

QLineEdit:focus {
    border: 1px solid #5a6e85;
    background-color: #1c1f22;
}

QLineEdit::placeholder {
    color: #525866;
}

/* Botão Salvar (Azul Slate Dessaturado) */
QPushButton {
    background-color: #3f546c;
    color: #f3f4f6;
    font-weight: 600;
    font-size: 13px;
    border-radius: 4px;
    padding: 9px 16px;
    border: none;
}

QPushButton:hover {
    background-color: #4a637f;
}

QPushButton:pressed {
    background-color: #334458;
}

/* Botão Limpar */
QPushButton#btn_limpar {
    background-color: #2a2e33;
    color: #9ca3af;
    border: 1px solid #363a40;
    font-weight: 600;
}

QPushButton#btn_limpar:hover {
    background-color: #32363d;
    color: #e5e7eb;
}

/* Botão CEP */
QPushButton#btn_cep {
    background-color: #2a2e33;
    color: #94a3b8;
    border: 1px solid #3a4556;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton#btn_cep:hover {
    background-color: #3f546c;
    color: #ffffff;
}

QFrame#divisor {
    background-color: #2e3238;
    max-height: 1px;
}
"""

class DatabaseManager:
    """Gerencia a conexão e armazenamento no banco SQLite."""
    def __init__(self, db_name="alkimins_cadastro.db"):
        self.db_name = db_name
        self.create_table()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def create_table(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        documento TEXT NOT NULL,
                        email TEXT NOT NULL,
                        celular TEXT NOT NULL,
                        cep TEXT NOT NULL,
                        logradouro TEXT NOT NULL,
                        numero TEXT NOT NULL,
                        complemento TEXT,
                        bairro TEXT NOT NULL,
                        cidade TEXT NOT NULL,
                        estado TEXT NOT NULL
                    )
                ''')
                conn.commit()
        except sqlite3.Error as e:
            print(f"Erro no banco SQLite: {e}")

    def salvar_cadastro(self, dados: tuple) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO clientes (
                        nome, documento, email, celular, cep, 
                        logradouro, numero, complemento, bairro, cidade, estado
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', dados)
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Erro ao salvar registro: {e}")
            return False


class Validador:
    
    @staticmethod
    def validar_email(email: str) -> bool:
        padrao = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(padrao, email) is not None

    @staticmethod
    def validar_celular(celular: str) -> bool:
        numeros = re.sub(r'\D', '', celular)
        return len(numeros) == 11

    @staticmethod
    def validar_cep(cep: str) -> bool:
        numeros = re.sub(r'\D', '', cep)
        return len(numeros) == 8

    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        cpf = re.sub(r'\D', '', cpf)
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        for i in range(9, 11):
            soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(0, i))
            digito = (soma * 10) % 11
            if digito == 10:
                digito = 0
            if digito != int(cpf[i]):
                return False
        return True

    @staticmethod
    def validar_cnpj(cnpj: str) -> bool:
        cnpj = re.sub(r'\D', '', cnpj)
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        
        soma1 = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
        digito1 = 11 - (soma1 % 11)
        digito1 = 0 if digito1 >= 10 else digito1
        if int(cnpj[12]) != digito1:
            return False
            
        soma2 = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
        digito2 = 11 - (soma2 % 11)
        digito2 = 0 if digito2 >= 10 else digito2
        if int(cnpj[13]) != digito2:
            return False
            
        return True

    @staticmethod
    def validar_documento(doc: str) -> tuple[bool, str]:
        numeros = re.sub(r'\D', '', doc)
        if len(numeros) == 11:
            if Validador.validar_cpf(numeros):
                return True, "CPF"
            return False, "CPF informado é inválido."
        elif len(numeros) == 14:
            if Validador.validar_cnpj(numeros):
                return True, "CNPJ"
            return False, "CNPJ informado é inválido."
        else:
            return False, "Informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido."


class AlkimiApp(QWidget):
    """Interface desktop profissional e ergonômica."""
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()

    def criar_campo(self, rotulo: str, placeholder: str = "") -> tuple[QWidget, QLineEdit]:
        """Gera um bloco com rótulo e campo perfeitamente alinhados."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel(rotulo)
        input_field = QLineEdit()
        if placeholder:
            input_field.setPlaceholderText(placeholder)

        layout.addWidget(label)
        layout.addWidget(input_field)
        return container, input_field

    def init_ui(self):
        self.setWindowTitle("Alkimin's - Gestão de Clientes")
        self.resize(580, 660)
        self.setStyleSheet(ALKIMINS_STYLE)

        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(14)
        layout_principal.setContentsMargins(24, 20, 24, 24)

        # Cabeçalho
        header_container = QWidget()
        layout_header = QVBoxLayout(header_container)
        layout_header.setContentsMargins(0, 0, 0, 0)
        layout_header.setSpacing(2)

        titulo = QLabel("Alkimin's")
        titulo.setStyleSheet("font-size: 20px; font-weight: 700; color: #e2e8f0;")
        
        subtitulo = QLabel("Painel de Cadastro de Clientes")
        subtitulo.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 500;")

        layout_header.addWidget(titulo)
        layout_header.addWidget(subtitulo)

        divisor = QFrame()
        divisor.setObjectName("divisor")
        divisor.setFrameShape(QFrame.HLine)

        layout_principal.addWidget(header_container)
        layout_principal.addWidget(divisor)

        # Dados Pessoais
        box_pessoais = QGroupBox("DADOS PESSOAIS")
        grid_pessoais = QGridLayout(box_pessoais)
        grid_pessoais.setHorizontalSpacing(12)
        grid_pessoais.setVerticalSpacing(10)

        c_nome, self.input_nome = self.criar_campo("Nome Completo *", "Digite o nome completo")
        c_doc, self.input_doc = self.criar_campo("CPF / CNPJ *", "Apenas números")
        c_email, self.input_email = self.criar_campo("E-mail *", "nome@dominio.com")
        c_cel, self.input_celular = self.criar_campo("Celular *", "11999999999")

        # Campo CEP com busca integrada
        c_cep = QWidget()
        l_cep = QVBoxLayout(c_cep)
        l_cep.setContentsMargins(0, 0, 0, 0)
        l_cep.setSpacing(4)
        l_cep.addWidget(QLabel("CEP *"))

        sub_cep = QHBoxLayout()
        sub_cep.setSpacing(8)
        self.input_cep = QLineEdit()
        self.input_cep.setPlaceholderText("00000000")
        self.btn_buscar_cep = QPushButton("Buscar CEP")
        self.btn_buscar_cep.setObjectName("btn_cep")
        self.btn_buscar_cep.clicked.connect(self.buscar_cep)

        sub_cep.addWidget(self.input_cep)
        sub_cep.addWidget(self.btn_buscar_cep)
        l_cep.addLayout(sub_cep)

        grid_pessoais.addWidget(c_nome, 0, 0, 1, 2)
        grid_pessoais.addWidget(c_doc, 1, 0)
        grid_pessoais.addWidget(c_email, 1, 1)
        grid_pessoais.addWidget(c_cel, 2, 0)
        grid_pessoais.addWidget(c_cep, 2, 1)

        # Endereço
        box_endereco = QGroupBox("ENDEREÇO")
        grid_endereco = QGridLayout(box_endereco)
        grid_endereco.setHorizontalSpacing(12)
        grid_endereco.setVerticalSpacing(10)

        c_log, self.input_logradouro = self.criar_campo("Logradouro *", "Rua, Avenida, etc.")
        c_num, self.input_numero = self.criar_campo("Número *", "Ex: 123")
        c_comp, self.input_complemento = self.criar_campo("Complemento", "Apto, Bloco...")
        c_bairro, self.input_bairro = self.criar_campo("Bairro *", "Nome do bairro")
        c_cidade, self.input_cidade = self.criar_campo("Cidade *", "Nome da cidade")
        c_uf, self.input_estado = self.criar_campo("UF *", "SP")

        grid_endereco.addWidget(c_log, 0, 0, 1, 3)
        grid_endereco.addWidget(c_num, 1, 0)
        grid_endereco.addWidget(c_comp, 1, 1)
        grid_endereco.addWidget(c_bairro, 1, 2)
        grid_endereco.addWidget(c_cidade, 2, 0, 1, 2)
        grid_endereco.addWidget(c_uf, 2, 2)

        layout_principal.addWidget(box_pessoais)
        layout_principal.addWidget(box_endereco)

        # Botões de Controle
        layout_botoes = QHBoxLayout()
        layout_botoes.setSpacing(12)

        self.btn_limpar = QPushButton("Limpar Campos")
        self.btn_limpar.setObjectName("btn_limpar")
        self.btn_salvar = QPushButton("Salvar Cliente")

        self.btn_salvar.clicked.connect(self.processar_cadastro)
        self.btn_limpar.clicked.connect(self.limpar_formulario)

        layout_botoes.addWidget(self.btn_limpar, 1)
        layout_botoes.addWidget(self.btn_salvar, 2)

        layout_principal.addLayout(layout_botoes)

    def buscar_cep(self):
        cep = self.input_cep.text().strip()
        if not Validador.validar_cep(cep):
            QMessageBox.warning(self, "Alkimin's", "Informe um CEP válido com 8 números.")
            return

        cep_limpo = re.sub(r'\D', '', cep)
        try:
            response = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5)
            dados = response.json()

            if "erro" in dados and dados["erro"] is True:
                QMessageBox.warning(self, "Alkimin's", "CEP não localizado.")
                return

            self.input_logradouro.setText(dados.get("logradouro", ""))
            self.input_bairro.setText(dados.get("bairro", ""))
            self.input_cidade.setText(dados.get("localidade", ""))
            self.input_estado.setText(dados.get("uf", ""))
            
            QMessageBox.information(self, "Alkimin's", "Endereço localizado com sucesso!")
            
        except requests.exceptions.RequestException:
            QMessageBox.critical(self, "Alkimin's", "Falha ao conectar com o serviço de CEP.")

    def processar_cadastro(self):
        nome = self.input_nome.text().strip()
        doc = self.input_doc.text().strip()
        email = self.input_email.text().strip()
        celular = self.input_celular.text().strip()
        cep = self.input_cep.text().strip()
        logradouro = self.input_logradouro.text().strip()
        numero = self.input_numero.text().strip()
        complemento = self.input_complemento.text().strip()
        bairro = self.input_bairro.text().strip()
        cidade = self.input_cidade.text().strip()
        estado = self.input_estado.text().strip()

        if not all([nome, doc, email, celular, cep, logradouro, numero, bairro, cidade, estado]):
            QMessageBox.warning(self, "Alkimin's", "Preencha todos os campos obrigatórios (*).")
            return

        doc_valido, msg_doc = Validador.validar_documento(doc)
        if not doc_valido:
            QMessageBox.warning(self, "Alkimin's", msg_doc)
            return

        if not Validador.validar_email(email):
            QMessageBox.warning(self, "Alkimin's", "E-mail em formato inválido.")
            return

        if not Validador.validar_celular(celular):
            QMessageBox.warning(self, "Alkimin's", "O celular deve conter 11 dígitos com DDD.")
            return

        dados = (nome, doc, email, celular, cep, logradouro, numero, complemento, bairro, cidade, estado)
        if self.db.salvar_cadastro(dados):
            QMessageBox.information(self, "Alkimin's", "Cliente cadastrado com sucesso!")
            self.limpar_formulario()
        else:
            QMessageBox.critical(self, "Alkimin's", "Falha ao gravar no banco de dados.")

    def limpar_formulario(self):
        self.input_nome.clear()
        self.input_doc.clear()
        self.input_email.clear()
        self.input_celular.clear()
        self.input_cep.clear()
        self.input_logradouro.clear()
        self.input_numero.clear()
        self.input_complemento.clear()
        self.input_bairro.clear()
        self.input_cidade.clear()
        self.input_estado.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = AlkimiApp()
    janela.show()
    sys.exit(app.exec())