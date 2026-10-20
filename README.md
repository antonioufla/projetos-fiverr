# projetos-fiverr

Monorepo privado com os projetos de clientes do Fiverr (@antoniorochanet).

## Estrutura

```
clientes/
  <usuario-fiverr>-<projeto>/   # um projeto por pasta
    PROJETO.md                  # cliente, pedido, escopo, prazo, status
    app/                        # código da entrega
    deploy.env                  # subdomínio e porta do deploy
  _modelo/                      # modelo para copiar ao iniciar um projeto
infra/
  deploy/                       # scripts e configs do servidor (Docker + proxy com SSL)
```

## Convenções

- **Nome da pasta:** `<usuario-fiverr>-<projeto>`, em minúsculas, com `-` no lugar de espaço e de `_`. Exemplo: `johnsmith-chatbot-suporte`.
- **Entrega online:** cada projeto vai para `https://<nome-da-pasta>.<dominio-principal>`.
- **Deploy:** só a pasta que mudou é publicada.
- **Código para o cliente:** se o cliente pedir o código-fonte, a pasta dele é extraída para um repositório próprio.
- Nada de segredos (chaves de API, senhas) no repositório. Eles ficam só no servidor.
