from flask import Flask, render_template, request, send_file
import io
from datetime import datetime

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Campos esperados no formulário
        campos = [
            "debito_maquina", "credito_maquina", "qrcode_maquina",
            "debito_consumer", "credito_consumer",
            "qrcode_consumer", "pix_consumer", "despesas",
            "dinheiro_consumer", "dinheiro_planilha",
            "total_fiado_vendas", "total_fiado_pagos", "dinheiro_contado", "saldo_inicial"
        ]

        # Captura e converte os dados para float, ou zero se vazio
        dados = {campo: float(request.form.get(campo) or 0) for campo in campos}
        dados["data"] = request.form.get("data") or datetime.now().strftime("%d/%m/%Y")

        # --- Cálculo do Dinheiro resumido ---
        dinheiro = dados["dinheiro_planilha"] + dados["dinheiro_consumer"]
        
        dinheiroConferido = dados["saldo_inicial"] + dados["dinheiro_contado"] + dados["despesas"]

        # --- Cálculo do total de vendas ---
        total_vendas = (
            dados["debito_maquina"] + dados["credito_maquina"] + dados["qrcode_maquina"] +
            dados["pix_consumer"] + dinheiro
        )

        # Total líquido
        liquido = total_vendas - dados["despesas"]

        # Diferenças entre máquina x consumer
        diferencas = {
            "Débito": round(dados["debito_consumer"] - dados["debito_maquina"], 2),
            "Crédito": round(dados["credito_consumer"] - dados["credito_maquina"], 2),
            "QR Code": round(dados["qrcode_consumer"] - dados["qrcode_maquina"], 2),
        }
        diferencas_existentes = {k: v for k, v in diferencas.items() if abs(v) > 0.009}

        # Novos cálculos
        total_vendas_fiado = total_vendas + dados["total_fiado_vendas"]
        total_liquido_fiado_pg = liquido + dados["total_fiado_pagos"]

        # Monta o texto do fechamento
        txt = io.StringIO()
        txt.write("********** FECHAMENTO DE CAIXA **********\n")
        txt.write(f"DATA: {dados['data']}\n")
        txt.write("-----------------------------------------\n")
        txt.write(f"DÉBITO..................: R$ {dados['debito_maquina']:.2f}\n")
        txt.write(f"CRÉDITO.................: R$ {dados['credito_maquina']:.2f}\n")
        txt.write(f"QR CODE.................: R$ {dados['qrcode_maquina']:.2f}\n")
        txt.write(f"PIX.....................: R$ {dados['pix_consumer']:.2f}\n")
        txt.write(f"DINHEIRO................: R$ {dinheiro:.2f}\n\n")
        txt.write(f"VENDAS FIADO............: R$ {dados['total_fiado_vendas']:.2f}\n")
        txt.write(f"FIADOS PAGOS............: R$ {dados['total_fiado_pagos']:.2f}\n\n")

        txt.write(f"DESPESAS................: R$ {dados['despesas']:.2f}\n")
        txt.write("-----------------------------------------\n")
        txt.write(f"TOTAL VENDAS............: R$ {total_vendas:.2f}\n")
        txt.write(f"TOTAL VENDAS + FIADO....: R$ {total_vendas_fiado:.2f}\n\n")
            
        
        txt.write(f"VALOR LÍQUIDO...........: R$ {liquido:.2f}\n")
        txt.write(f"TOTAL LÍQUIDO + FIADO PG: R$ {total_liquido_fiado_pg:.2f}\n")
        if dinheiroConferido != dinheiro:
            txt.write(f"\nDIFERENÇA DINHEIRO......: R$ {dinheiroConferido - dinheiro:.2f}\n")
        txt.write("-----------------------------------------\n")

        if diferencas_existentes:
            txt.write("\nDiferenças:\n")
            for k, v in diferencas_existentes.items():
                txt.write(f"-> {k}: R$ {v:.2f}\n")

        txt.write("*****************************************\n")

        # Cria um arquivo em memória
        buffer = io.BytesIO()
        buffer.write(txt.getvalue().encode("utf-8"))
        buffer.seek(0)

        # Nome do arquivo com a data
        filename = f"fechamento_{dados['data'].replace('/', '-')}.txt"

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="text/plain"
        )

    return render_template("form.html", caixa=None)


if __name__ == "__main__":
    app.run(debug=True)
