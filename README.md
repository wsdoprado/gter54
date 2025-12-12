# gter54 - Do Git ao Router

Projeto de automação de rede demonstrando um pipeline completo desde o Git até o deployment em roteadores, apresentado no GTER54.

## 📋 Visão Geral

Este projeto demonstra práticas modernas de NetDevOps integrando:

- **NetBox** como Network Source of Truth (NSOT)
- **Git** para controle de versão e triggers de CI/CD
- **Gitea Actions** para automação de pipeline
- **ContainerLab** com dispositivos Nokia SR Linux para digital twin
- **NUTS** (Network Unit Testing System) para validação automatizada

## 🏗️ Arquitetura

```
NetBox → feature → development → main
           ↓           ↓           ↓
        Commit    CD Validation  Deploy
                  (Digital Twin) (Production)
```

### Topologia de Rede

- 3 dispositivos PE (Provider Edge) Nokia SR Linux
- Topologia OSPF
- Testes automatizados de interfaces, conectividade ICMP e neighbors OSPF

## 🚀 Pré-requisitos

- Sistema operacional: Linux (recomendado Ubuntu/Debian)
- Docker e Docker Compose
- Acesso root ou sudo para ContainerLab

## 📦 Instalação

### 1. Instalar ContainerLab

ContainerLab é necessário para criar e gerenciar o ambiente de digital twin com dispositivos de rede.

```bash
# Download e instalação do ContainerLab
bash -c "$(curl -sL https://get.containerlab.dev)"

# Verificar instalação
containerlab version
```

**Documentação oficial:** https://containerlab.dev/install/

### 2. Instalar UV (Python Package Manager)

UV é um gerenciador de pacotes Python moderno e rápido, usado para gerenciar as dependências do projeto.

```bash
# Instalação via curl
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ou via pip
pip install uv

# Verificar instalação
uv --version
```

**Documentação oficial:** https://docs.astral.sh/uv/

### 3. Clonar o Repositório

```bash
git clone <repository-url>
cd gter54
```

### 4. Instalar Dependências Python

```bash
# Criar ambiente virtual e instalar dependências
uv venv .venv
source .venv/bin/activate
uv sync

```

## 🔧 Configuração

### NetBox

1. Configure o NetBox com os dispositivos PE1, PE2, PE3
2. Configure os templates de configuração para SR Linux
3. Configure as interfaces e endereços IP conforme a topologia

### Gitea

1. Configure o repositório no Gitea
2. Configure o Gitea Actions runner com acesso privilegiado ao Docker
3. Configure os secrets necessários:
   - `NETBOX_URL`: URL da API do NetBox
   - `NETBOX_TOKEN`: Token de acesso ao NetBox

### Docker Compose (para Gitea Runner)

Exemplo de configuração para o runner com acesso ao ContainerLab:

```yaml
services:
  runner:
    image: gitea/act_runner:latest
    privileged: true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/data
    environment:
      - GITEA_INSTANCE_URL=http://gitea:3000
      - GITEA_RUNNER_REGISTRATION_TOKEN=${REGISTRATION_TOKEN}
```

## 🧪 Executando os Testes

### Localmente

```bash
# Deploy da topologia ContainerLab
sudo containerlab deploy -t topology.yml

# Executar testes NUTS
uv run pytest tests/

# Destruir a topologia
sudo containerlab destroy -t topology.yml
```

### Via CI/CD Pipeline

O pipeline é acionado automaticamente:

- **feature → development**: Pull Request aciona pipeline de validação
- **development → main**: Merge aciona pipeline de deploy

## 📂 Estrutura do Projeto

```
gter54/
├── .gitea/
│   └── workflows/
│       └── ci.yml           # Pipeline CI/CD
├── configs/                  # Configurações geradas do NetBox
│   ├── pe1.conf
│   ├── pe2.conf
│   └── pe3.conf
├── tests/                    # Testes NUTS
│   ├── test_interfaces.yml
│   ├── test_icmp.yml
│   └── test_ospf.yml
├── topology.yml              # Topologia ContainerLab
├── pyproject.toml           # Dependências Python
└── README.md
```

## 🔄 Workflow de Desenvolvimento

1. **Feature Branch**: NetBox gera configurações e cria commit na branch feature
2. **Pull Request**: Abre PR de feature → development
3. **Validação**: Pipeline executa testes no digital twin (ContainerLab)
4. **Merge to Development**: Após validação, merge para development
5. **Deploy**: Merge de development → main aciona deploy para produção

## 🧩 Componentes Principais

### NUTS (Network Unit Testing System)

Framework de testes para dispositivos de rede que valida:
- Configuração de interfaces
- Conectividade ICMP
- Adjacências OSPF
- Estado operacional dos dispositivos

### ContainerLab

Cria ambientes de laboratório usando containers Docker para:
- Simular topologias de rede completas
- Testar configurações antes do deploy
- Validar mudanças em ambiente controlado

### NetBox

Fonte da verdade (NSOT) que mantém:
- Inventário de dispositivos
- Configuração de interfaces
- Endereçamento IP
- Templates de configuração

## 🐛 Troubleshooting

### ContainerLab não inicia

```bash
# Verificar se o Docker está rodando
sudo systemctl status docker

# Verificar permissões
sudo usermod -aG docker $USER
```

### Testes NUTS falhando

```bash
# Verificar conectividade com os dispositivos
sudo containerlab inspect -t topology.yml

# Verificar logs dos containers
docker logs <container-id>
```

### Pipeline CI/CD com erros

```bash
# Verificar logs do runner
docker logs gitea-runner

# Verificar permissões do runner para acessar Docker socket
ls -la /var/run/docker.sock
```

## 📚 Recursos Adicionais

- [ContainerLab Documentation](https://containerlab.dev/)
- [Nokia SR Linux Documentation](https://documentation.nokia.com/srlinux/)
- [NetBox Documentation](https://docs.netbox.dev/)
- [NUTS Framework](https://nuts.network/)
- [Gitea Actions](https://docs.gitea.io/en-us/actions/)

## 📄 Licença

[Especificar licença do projeto]

## 📧 Contato

William - [informações de contato]

---

**Apresentação GTER54**: "Do Git ao Router - Automação de Rede com NetDevOps"
