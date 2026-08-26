import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

def gerar_pdf_ata(texto_minuta: str, titulo_documento: str = "MINUTA DE ATA") -> bytes:
    """
    Converte o texto da minuta num documento PDF devidamente formatado.
    Devolve os dados do PDF em bytes para ser descarregado no Streamlit.
    """
    buffer = io.BytesIO()
    
    # Configuração do documento A4 com margens de 2.5 cm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm
    )

    story = []
    styles = getSampleStyleSheet()

    # Estilo do Título Principal
    estilo_titulo = ParagraphStyle(
        name='TituloAta',
        parent=styles['Heading1'],
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName='Helvetica-Bold'
    )

    # Estilo do Corpo do Texto (Justificado e com espaçamento entre parágrafos)
    estilo_corpo = ParagraphStyle(
        name='CorpoAta',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        fontName='Helvetica'
    )

    # Adicionar Título
    story.append(Paragraph(titulo_documento.upper(), estilo_titulo))
    story.append(Spacer(1, 10))

    # Processar o texto linha a linha / parágrafo a parágrafo
    paragrafos = texto_minuta.split('\n')
    for p in paragrafos:
        texto_limpo = p.strip()
        if texto_limpo:
            # Substitui quebras de linha manuais em HTML seguro para o ReportLab
            texto_formatado = texto_limpo.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(texto_formatado, estilo_corpo))

    # Construir o PDF na memória
    doc.build(story)
    
    # Obter os bytes do PDF
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes