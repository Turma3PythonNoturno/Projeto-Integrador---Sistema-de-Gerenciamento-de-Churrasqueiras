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
    PIX_KEY = "03230664108"  # Pode ser CPF, CNPJ, telefone, email ou chave aleatória
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
        """Gera string de dados Pix com padrão EMV correto"""
        
        # Identificador único da transação
        identificador_unico = f"TAXA{taxa_id:06d}"
        
        # Formatar valor com 2 casas decimais
        valor_str = f"{float(valor):.2f}"
        
        # Obter dados configurados
        chave_pix = QRCodeService.PIX_KEY
        merchant_name = QRCodeService.MERCHANT_NAME[:25]  # Máximo 25 caracteres
        merchant_city = QRCodeService.MERCHANT_CITY[:15]  # Máximo 15 caracteres
        
        # Construir payload no formato EMV (Tag-Length-Value)
        
        # Tag 26: Merchant Account Information
        gui = "br.gov.bcb.pix"
        tag_00 = f"00{len(gui):02d}{gui}"
        tag_01 = f"01{len(chave_pix):02d}{chave_pix}"
        tag_26_content = tag_00 + tag_01
        tag_26 = f"26{len(tag_26_content):02d}{tag_26_content}"
        
        # Tag 52: Merchant Category Code (0000 para pessoa física)
        tag_52 = "52040000"
        
        # Tag 53: Transaction Currency (986 = BRL)
        tag_53 = "5303986"
        
        # Tag 54: Transaction Amount
        tag_54 = f"54{len(valor_str):02d}{valor_str}"
        
        # Tag 58: Country Code
        tag_58 = "5802BR"
        
        # Tag 59: Merchant Name
        tag_59 = f"59{len(merchant_name):02d}{merchant_name}"
        
        # Tag 60: Merchant City
        tag_60 = f"60{len(merchant_city):02d}{merchant_city}"
        
        # Tag 62: Additional Data Field Template (txid)
        tag_05 = f"05{len(identificador_unico):02d}{identificador_unico}"
        tag_62 = f"62{len(tag_05):02d}{tag_05}"
        
        # Montar payload sem CRC
        payload = f"000201{tag_26}{tag_52}{tag_53}{tag_54}{tag_58}{tag_59}{tag_60}{tag_62}6304"
        
        # Calcular CRC16 CCITT
        crc = QRCodeService._calcular_crc16(payload)
        
        # Payload final com CRC
        pix_string = f"{payload}{crc}"
        
        return pix_string
    
    @staticmethod
    def _calcular_crc16(payload: str) -> str:
        """Calcula CRC16 CCITT (polinômio 0x1021) para validação Pix"""
        crc = 0xFFFF
        for char in payload:
            crc ^= ord(char) << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                crc &= 0xFFFF
        return f"{crc:04X}"
    
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
