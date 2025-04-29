import psycopg2
import sys

def testar_conexao():
    print("Testando conexão final com PostgreSQL...")
    
    try:
        # Conectar ao banco de dados
        conn = psycopg2.connect(
            "postgresql://denisbonaccini:7ce3284bA@localhost:5432/deteco"
        )
        
        # Criar cursor
        cur = conn.cursor()
        
        # Verificar versão
        cur.execute("SELECT version()")
        versao = cur.fetchone()[0]
        print(f"PostgreSQL versão: {versao}")
        
        # Verificar tabelas no banco
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tabelas = cur.fetchall()
        
        print("\nTabelas disponíveis:")
        for tabela in tabelas:
            print(f"- {tabela[0]}")
        
        # Verificar estrutura da tabela users
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users'")
        colunas = cur.fetchall()
        
        print("\nEstrutura da tabela users:")
        for coluna in colunas:
            print(f"- {coluna[0]} ({coluna[1]})")
        
        # Fechar conexão
        conn.close()
        print("\nConexão com PostgreSQL bem-sucedida!")
        return True
        
    except Exception as e:
        print(f"ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    resultado = testar_conexao()
    sys.exit(0 if resultado else 1) 