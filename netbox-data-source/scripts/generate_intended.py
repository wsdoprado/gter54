from extras.scripts import Script, ObjectVar, BooleanVar, StringVar
from dcim.models import Device
import base64
import requests
from datetime import datetime
import difflib

class RenderAndPushConfig(Script):
    """
    Script para renderizar configuração de um device e enviar para o Gitea
    """
    
    class Meta:
        name = "Render Config and Push to Git"
        description = "Renderiza a configuração do device e faz commit no Gitea"
        commit_default = False
    
    # Campo para selecionar o device
    device = ObjectVar(
        model=Device,
        required=True,
        description="Selecione o dispositivo"
    )
    
    # Opção para apenas visualizar (não fazer push)
    dry_run = BooleanVar(
        default=False,
        description="Apenas visualizar (não enviar para Git)"
    )
    
    def run(self, data, commit):
        device = data['device']
        dry_run = data.get('dry_run', False)
        
        self.log_info("=" * 70)
        self.log_info(f"📡 Device: {device.name}")
        self.log_info(f"   Site: {device.site.name if device.site else 'N/A'}")
        self.log_info(f"   Tipo: {device.device_type.model if device.device_type else 'N/A'}")
        self.log_info("=" * 70)
        self.log_info("")
        
        # ========================================
        # PASSO 1: RENDERIZAR CONFIGURAÇÃO
        # ========================================
        
        if not device.config_template:
            self.log_failure("❌ Este device não possui um Config Template associado!")
            self.log_warning("💡 Associe um Config Template ao device para continuar")
            return
        
        self.log_success(f"✓ Config Template: {device.config_template.name}")
        
        try:
            self.log_info("🔄 Renderizando configuração...")
            rendered_config = device.config_template.render(context={'device': device})
            
            self.log_success("✓ Configuração renderizada com sucesso!")
            self.log_info("")
            self.log_info("─" * 70)
            self.log_info(f"Total de linhas: {len(rendered_config.split(chr(10)))}")
            self.log_info("")
            
        except Exception as e:
            self.log_failure(f"❌ Erro ao renderizar: {str(e)}")
            return
        
        # ========================================
        # PASSO 2: ENVIAR PARA GITEA
        # ========================================
        
        if dry_run:
            self.log_warning("🔍 Modo DRY-RUN ativado - não será feito commit no Git")
            return
        
        self.log_info("=" * 70)
        self.log_info("📤 ENVIANDO PARA GITEA")
        self.log_info("=" * 70)
        
        # Configurações do Gitea
        GITEA_URL = "http://192.168.246.95:3000"
        REPO = "wprado/gter54"
        TOKEN = "ed2a927949252a4e9f91b18fab05f6315e3e1ee5"
        BRANCH = "main"
        
        headers = {"Authorization": f"token {TOKEN}"}
        filename = f"netbox-data-source/intended/{device.name}.cfg"
        
        self.log_info(f"🔗 URL: {GITEA_URL}")
        self.log_info(f"📁 Repo: {REPO}")
        self.log_info(f"🌿 Branch: {BRANCH}")
        self.log_info(f"📄 Arquivo: {filename}")
        self.log_info("")
        
        # Verificar se arquivo já existe
        url_get = f"{GITEA_URL}/api/v1/repos/{REPO}/contents/{filename}"
        
        try:
            resp_get = requests.get(url_get, headers=headers, params={"ref": BRANCH})
            sha = None
            
            if resp_get.status_code == 200:
                sha = resp_get.json().get("sha")
                existing_content_b64 = resp_get.json().get("content", "")
                existing_content = base64.b64decode(existing_content_b64).decode()
                
                # Comparar conteúdos
                if existing_content.strip() == rendered_config.strip():
                    self.log_warning("⚠️  Arquivo já existe e está idêntico")
                    self.log_info("✓ Nenhuma alteração necessária - commit não será feito")
                    return
                
                self.log_info("📝 Arquivo existe - será atualizado")
                self.log_info("")
                self.log_info("🔍 DIFERENÇAS DETECTADAS:")
                self.log_info("─" * 70)
                
                # Mostrar diff
                diff = difflib.unified_diff(
                    existing_content.splitlines(keepends=True),
                    rendered_config.splitlines(keepends=True),
                    fromfile=f'{filename} (atual)',
                    tofile=f'{filename} (novo)',
                    lineterm=''
                )
                
                for line in diff:
                    self.log_info(line.rstrip())
                
                self.log_info("─" * 70)
                self.log_info("")
                
            elif resp_get.status_code == 404:
                self.log_info("📄 Arquivo não existe - será criado")
            else:
                self.log_failure(f"❌ Erro ao verificar arquivo: {resp_get.status_code}")
                self.log_failure(resp_get.text)
                return
            
            # Preparar payload para commit
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"NetBox: {device.name} - {timestamp}"
            
            payload = {
                "content": base64.b64encode(rendered_config.encode()).decode(),
                "message": commit_message,
                "branch": BRANCH
            }
            
            if sha:
                payload["sha"] = sha
            
            # Enviar para Gitea
            self.log_info(f"⏳ Enviando para Git...")
            
            if sha:
                resp = requests.put(url_get, headers=headers, json=payload)
            else:
                resp = requests.post(url_get, headers=headers, json=payload)
            
            if resp.status_code in [200, 201]:
                self.log_success("=" * 70)
                self.log_success("✓ COMMIT REALIZADO COM SUCESSO!")
                self.log_success("=" * 70)
                self.log_info(f"📝 Mensagem: {commit_message}")
                
                # Extrair URL do commit se disponível
                commit_data = resp.json()
                if 'commit' in commit_data:
                    commit_url = commit_data['commit'].get('html_url', '')
                    if commit_url:
                        self.log_info(f"🔗 Ver commit: {commit_url}")
                
            else:
                self.log_failure("=" * 70)
                self.log_failure("❌ FALHA AO FAZER COMMIT")
                self.log_failure("=" * 70)
                self.log_failure(f"Status: {resp.status_code}")
                self.log_failure(f"Resposta: {resp.text}")
                
        except requests.exceptions.RequestException as e:
            self.log_failure(f"❌ Erro de conexão com Gitea: {str(e)}")
        except Exception as e:
            self.log_failure(f"❌ Erro inesperado: {str(e)}")
            import traceback
            self.log_info(traceback.format_exc())
