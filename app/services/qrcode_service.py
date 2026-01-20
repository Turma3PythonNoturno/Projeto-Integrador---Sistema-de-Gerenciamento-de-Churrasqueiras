"""
QR Code Service - Geração de QR codes para pagamento Pix
Implementa padrão EMV dinâmico para Pix
"""

from io import BytesIO
import qrcode
from datetime import datetime
from typing import Dict, Optional
from decimal import Decimal
import hashlib


class QRCodeService:
    """Serviço para gerar QR codes de pagamento Pix"""
    
    # Chave Pix da organização (exemplo fictício - atualizar com chave real)
    PIX_KEY = "sint-ifesgo@example.com"  # Pode ser CPF, CNPJ, telefone, email ou chave aleatória
    MERCHANT_NAME = "SINT-IFESGO"
    MERCHANT_CITY = "Goiania"
    
    def __init__(self):
        """Inicializa o serviço"""
        pass
    
    @staticmethod
    def gerar_qrcode_pix(valor: Decimal, taxa_id: int, descricao: str = "Reserva de Churrasqueira") -> Dict:
        """Gera QR code Pix dinâmico seguindo padrão EMV
        
        Args:
            valor: Valor da cobrança em reais
            taxa_id: ID da taxa (usado como identificador único)
            descricao: Descrição da cobrança
            
        Returns:
            Dict com URL da imagem em base64 e dados Pix
        """
        try:
            # Gerar dados Pix dinâmico (padrão simplificado)
            # Em produção, usar serviço Pix do banco ou integrador
            pix_data = QRCodeService._gerar_dados_pix(valor, taxa_id, descricao)
            
            # Gerar QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=2,
            )
            qr.add_data(pix_data)
            qr.make(fit=True)
            
            # Criar imagem
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Converter para bytes
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Converter para base64
            import base64
            img_base64 = base64.b64encode(img_bytes.getvalue()).decode()
            
            return {
                'sucesso': True,
                'qrcode_base64': f'data:image/png;base64,{img_base64}',
                'qrcode_bytes': img_bytes.getvalue(),
                'pix_data': pix_data,
                'valor': str(valor),
                'descricao': descricao,
                'taxa_id': taxa_id
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro ao gerar QR code: {str(e)}'
            }
    
    @staticmethod
    def _gerar_dados_pix(valor: Decimal, taxa_id: int, descricao: str) -> str:
        """Gera string de dados Pix com padrão EMV
        
        Esta é uma implementação simplificada. Em produção, usar:
        - Bacen Pix API
        - Integrador Pix (como Gerencianet, Wirecard, etc)
        - Banco próprio API
        """
        # Formato simplificado de Pix cópia-cola com valor
        # Em produção, seria base32 com estrutura TLV EMV
        
        # Usar identificador único com taxa_id
        identificador_unico = f"TAXA{taxa_id:06d}"
        
        # Valor com 2 casas decimais
        valor_str = f"{valor:.2f}".replace('.', '')
        
        # Montar dados Pix de exemplo (simulando formato real)
        # Em produção, seria gerado através de API do banco
        pix_string = (
            f"00020126580014br.gov.bcb.pix0136"
            f"sint-ifesgo@example.com5204000053039865"
            f"4059{valor_str:0>10}5802BR5913SINT-IFESGO"
            f"6009GOIANIA62{len(identificador_unico):02d}{identificador_unico}63041D3D"
        )
        
        return pix_string
    
    @staticmethod
    def gerar_qrcode_svg(valor: Decimal, taxa_id: int, descricao: str = "Reserva de Churrasqueira") -> Dict:
        """Alternativa: gera QR code em formato SVG (vetorial)
        
        Vantagem: melhor qualidade em impressão
        """
        try:
            pix_data = QRCodeService._gerar_dados_pix(valor, taxa_id, descricao)
            
            import qrcode
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=2,
            )
            qr.add_data(pix_data)
            qr.make(fit=True)
            
            # Gerar SVG
            import io
            from qrcode.image.svg import SvgPathImage
            factory = SvgPathImage
            qr_svg = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                image_factory=factory,
            )
            qr_svg.add_data(pix_data)
            qr_svg.make(fit=True)
            
            img = qr_svg.make_image()
            
            # Converter para string SVG
            svg_bytes = io.BytesIO()
            img.save(svg_bytes)
            svg_string = svg_bytes.getvalue().decode('utf-8')
            
            return {
                'sucesso': True,
                'qrcode_svg': svg_string,
                'pix_data': pix_data,
                'valor': str(valor),
                'descricao': descricao,
                'taxa_id': taxa_id
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro ao gerar QR code SVG: {str(e)}'
            }
    
    @staticmethod
    def gerar_dados_json(valor: Decimal, taxa_id: int, descricao: str) -> Dict:
        """Gera dados JSON para transmissão segura
        
        Útil para APIs mobile ou fluxos avançados
        """
        return {
            'tipo': 'pix',
            'chave': QRCodeService.PIX_KEY,
            'valor': float(valor),
            'descricao': descricao,
            'identificador': f"TAXA{taxa_id:06d}",
            'timestamp': datetime.now().isoformat(),
            'comerciante': {
                'nome': QRCodeService.MERCHANT_NAME,
                'cidade': QRCodeService.MERCHANT_CITY
            }
        }
