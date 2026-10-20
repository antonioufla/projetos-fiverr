"""Base de conhecimento da Clinica Sorriso (empresa ficticia) e busca por similaridade.

Cada intencao tem palavras-chave em PT e EN. A busca normaliza o texto (minusculas,
sem acentos), compara palavra a palavra com tolerancia a erros de digitacao (difflib)
e escolhe a intencao com maior pontuacao.
"""
import difflib
import re
import unicodedata

CLINICA = {
    "nome": "Clínica Sorriso",
    "endereco": "Av. Paulista, 1000, sala 52, São Paulo (SP)",
    "telefone": "(11) 4000-1234",
}

INTENCOES = [
    {
        "id": "saudacao",
        "chaves": "oi ola ola bom dia boa tarde boa noite hey hello hi hola eae opa tudo bem",
        "pt": "Olá! 😊 Sou a assistente virtual da Clínica Sorriso. Posso te ajudar com preços, horários, convênios, endereço ou agendamento. O que você precisa?",
        "en": "Hi! 😊 I'm Clínica Sorriso's virtual assistant. I can help with prices, opening hours, insurance, location or booking. What do you need?",
        "peso": 0.8,
    },
    {
        "id": "horario",
        "chaves": "horario horarios funcionamento abre fecha aberto sabado domingo feriado hora horas open opening hours close closed saturday sunday when time schedule",
        "pt": "🕘 Nosso horário:\n• Segunda a sexta: 8h às 19h\n• Sábado: 8h às 13h\n• Domingo e feriados: fechado (urgências pelo (11) 4000-1234)",
        "en": "🕘 Opening hours:\n• Monday to Friday: 8am to 7pm\n• Saturday: 8am to 1pm\n• Sundays and holidays: closed (emergencies: +55 11 4000-1234)",
    },
    {
        "id": "precos",
        "chaves": "preco precos valor valores quanto custa custo tabela orcamento price prices cost costs how much fee fees pricing",
        "pt": "💰 Valores de referência:\n• Avaliação: grátis\n• Limpeza (profilaxia): R$ 180\n• Restauração (resina): a partir de R$ 220\n• Clareamento: R$ 890\n• Canal: a partir de R$ 750\n• Implante: a partir de R$ 2.900\n• Aparelho: a partir de R$ 180/mês\nO valor final é definido na avaliação. Quer agendar?",
        "en": "💰 Reference prices:\n• Check-up: free\n• Cleaning: R$ 180\n• Filling (resin): from R$ 220\n• Whitening: R$ 890\n• Root canal: from R$ 750\n• Implant: from R$ 2,900\n• Braces: from R$ 180/month\nFinal price is confirmed at the check-up. Want to book?",
    },
    {
        "id": "limpeza",
        "chaves": "limpeza profilaxia tartaro placa cleaning clean tartar plaque",
        "pt": "🪥 A limpeza (profilaxia) custa R$ 180 e leva cerca de 40 minutos. Inclui remoção de tártaro, polimento e aplicação de flúor. Recomendamos a cada 6 meses.",
        "en": "🪥 A professional cleaning costs R$ 180 and takes about 40 minutes. It includes tartar removal, polishing and fluoride. We recommend it every 6 months.",
    },
    {
        "id": "clareamento",
        "chaves": "clareamento clarear branco brancos dentes amarelados whitening whiten white bleaching yellow",
        "pt": "✨ O clareamento custa R$ 890 (consultório + moldeira caseira). O resultado aparece em 2 a 3 semanas. Antes fazemos uma avaliação gratuita para ver se é indicado para você.",
        "en": "✨ Whitening costs R$ 890 (in-office + take-home trays). Results show in 2 to 3 weeks. We start with a free check-up to make sure it's right for you.",
    },
    {
        "id": "implante",
        "chaves": "implante implantes protese dente perdido faltando coroa implant implants missing tooth crown denture",
        "pt": "🦷 Implantes a partir de R$ 2.900 por dente (implante + coroa). O tratamento leva de 3 a 6 meses. Parcelamos em até 12x sem juros.",
        "en": "🦷 Implants from R$ 2,900 per tooth (implant + crown). Treatment takes 3 to 6 months. Up to 12 interest-free installments.",
    },
    {
        "id": "aparelho",
        "chaves": "aparelho ortodontia ortodontico alinhador invisivel invisalign braces orthodontic orthodontics aligner aligners straighten",
        "pt": "😁 Ortodontia: aparelho fixo a partir de R$ 180/mês e alinhadores transparentes a partir de R$ 6.500. A documentação inicial está inclusa na avaliação gratuita.",
        "en": "😁 Orthodontics: fixed braces from R$ 180/month and clear aligners from R$ 6,500. Initial records are included in the free check-up.",
    },
    {
        "id": "canal",
        "chaves": "canal endodontia dor dente doendo sensibilidade root canal pain toothache hurts sensitivity",
        "pt": "Tratamento de canal a partir de R$ 750. Se você está com dor agora, ligue para (11) 4000-1234: reservamos horários de urgência todos os dias.",
        "en": "Root canal from R$ 750. If you're in pain right now, call +55 11 4000-1234: we keep emergency slots every day.",
    },
    {
        "id": "urgencia",
        "chaves": "urgencia emergencia urgente quebrou quebrado inchado sangrando emergency urgent broken swollen bleeding",
        "pt": "🚨 Para urgências ligue agora para (11) 4000-1234. Temos horários reservados todos os dias e plantão por telefone aos domingos.",
        "en": "🚨 For emergencies call +55 11 4000-1234 now. We keep slots every day and phone support on Sundays.",
    },
    {
        "id": "convenio",
        "chaves": "convenio convenios plano planos odontologico amil bradesco sulamerica unimed odontoprev aceita insurance plan plans accept",
        "pt": "Atendemos os convênios Amil Dental, Bradesco Dental, SulAmérica Odonto e OdontoPrev. Também atendemos particular com desconto à vista.",
        "en": "We accept Amil Dental, Bradesco Dental, SulAmérica Odonto and OdontoPrev. Private patients get a discount for upfront payment.",
    },
    {
        "id": "pagamento",
        "chaves": "pagamento pagar parcelar parcela parcelas cartao pix dinheiro boleto juros desconto payment pay installments card credit cash discount",
        "pt": "💳 Aceitamos Pix, cartão de débito e crédito (até 12x sem juros) e dinheiro. Pagamento à vista no Pix tem 5% de desconto.",
        "en": "💳 We accept Pix, debit and credit cards (up to 12 interest-free installments) and cash. Upfront Pix payment gets 5% off.",
    },
    {
        "id": "endereco",
        "chaves": "endereco onde fica localizacao local chegar mapa estacionamento metro rua address where location located parking map directions subway",
        "pt": "📍 Av. Paulista, 1000, sala 52, São Paulo (SP), a 2 minutos do metrô Trianon-Masp. Temos convênio com o estacionamento do prédio.",
        "en": "📍 Av. Paulista, 1000, suite 52, São Paulo, 2 minutes from Trianon-Masp subway station. Discounted parking in the building.",
    },
    {
        "id": "agendar",
        "chaves": "agendar agendamento marcar consulta disponivel vaga avaliacao book booking appointment schedule visit available checkup",
        "pt": "📅 Para agendar, deixe seu nome e telefone com a recepção pelo (11) 4000-1234 ou pelo botão “Agendar avaliação” no topo da página. A primeira avaliação é grátis!",
        "en": "📅 To book, call reception at +55 11 4000-1234 or use the “Book a check-up” button at the top of the page. Your first check-up is free!",
    },
    {
        "id": "criancas",
        "chaves": "crianca criancas filho filha infantil bebe odontopediatria kid kids child children baby pediatric",
        "pt": "👶 Sim! Temos odontopediatra às terças e quintas, com consultório preparado para crianças a partir de 1 ano.",
        "en": "👶 Yes! Our pediatric dentist works Tuesdays and Thursdays, with an office designed for kids from age 1.",
    },
    {
        "id": "obrigado",
        "chaves": "obrigado obrigada valeu agradeco thanks thank thx tchau bye",
        "pt": "Por nada! 😊 Se precisar de mais alguma coisa, é só chamar.",
        "en": "You're welcome! 😊 Let me know if you need anything else.",
        "peso": 0.7,
    },
]

FALLBACK = {
    "pt": "Hmm, não tenho certeza sobre isso. 🤔 Posso ajudar com: preços, horários, convênios, formas de pagamento, endereço ou agendamento. Se preferir, fale com a recepção: (11) 4000-1234.",
    "en": "Hmm, I'm not sure about that. 🤔 I can help with: prices, opening hours, insurance, payment, location or booking. You can also call reception: +55 11 4000-1234.",
}

SUGESTOES = {
    "pt": ["Preços", "Horário", "Convênios", "Agendar avaliação"],
    "en": ["Prices", "Opening hours", "Insurance", "Book a check-up"],
}

PARADAS = set("a o e de da do das dos em no na um uma para por com que qual quais se meu minha voces vcs vc voce the a an is are do does to of for in on my your you i can it what".split())


def normalizar(txt: str) -> list[str]:
    txt = unicodedata.normalize("NFKD", txt.lower())
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return [p for p in re.findall(r"[a-z0-9]+", txt) if p not in PARADAS]


for _i in INTENCOES:
    _i["_chaves"] = set(normalizar(_i["chaves"]))
    _i["_frases"] = [" ".join(normalizar(f)) for f in ("bom dia", "boa tarde", "boa noite", "root canal", "how much", "quanto custa") if set(normalizar(f)) <= _i["_chaves"]]


def _pontuar(palavras: list[str], intencao: dict) -> float:
    pontos = 0.0
    for p in palavras:
        if p in intencao["_chaves"]:
            pontos += 1.0
        elif len(p) >= 4:
            m = difflib.get_close_matches(p, [c for c in intencao["_chaves"] if c[0] == p[0]], n=1, cutoff=0.8)
            if m:
                pontos += 0.75
    texto = " ".join(palavras)
    pontos += sum(0.5 for f in intencao["_frases"] if f in texto)
    return pontos * intencao.get("peso", 1.0)


def responder(mensagem: str, idioma: str = "pt") -> dict:
    idioma = "en" if idioma == "en" else "pt"
    palavras = normalizar(mensagem)
    ranking = sorted(((_pontuar(palavras, i), i) for i in INTENCOES), key=lambda x: -x[0])
    melhor_pts, melhor = ranking[0]
    if melhor_pts < 0.7:
        return {"resposta": FALLBACK[idioma], "intencao": None, "sugestoes": SUGESTOES[idioma]}
    # perguntas sobre preco de um servico especifico: o servico vence a tabela geral
    if melhor["id"] == "precos" and len(ranking) > 1 and ranking[1][0] >= 0.75 and ranking[1][1]["id"] not in ("saudacao", "obrigado", "agendar"):
        melhor = ranking[1][1]
    return {"resposta": melhor[idioma], "intencao": melhor["id"], "sugestoes": [] if melhor["id"] not in ("saudacao",) else SUGESTOES[idioma]}


def contexto_llm() -> str:
    """Base de conhecimento em texto, usada como contexto quando ha chave de LLM."""
    linhas = [f"Empresa: {CLINICA['nome']} (clinica odontologica ficticia de demonstracao)."]
    for i in INTENCOES:
        if i["id"] not in ("saudacao", "obrigado"):
            linhas.append(f"- {i['pt']}")
    return "\n".join(linhas)
