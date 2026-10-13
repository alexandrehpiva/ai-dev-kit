# Regras do C4 (fonte: c4model.com)

## Diagnóstico do modo de falha

O agente cita "o C4" de memória e mistura versões de blogs com o que o site oficial diz. Este asset registra o que as páginas oficiais afirmam (aspas = cópia literal, lida em 2026-10), separado do que é escolha desta skill. Atribuição: conteúdo de [c4model.com](https://c4model.com/) (Simon Brown), Creative Commons Attribution 4.0 International, segundo o rodapé do site.

## Abstrações

> "A software system is made up of one or more containers (applications and data stores), each of which contains one or more components, which in turn are implemented by one or more code elements (classes, interfaces, objects, functions, etc). And people (actors, roles, personas, named individuals, etc) use the software systems that we build."

| Abstração | Definição | Armadilha que a fonte cita |
|---|---|---|
| Pessoa | Atores, papéis, personas ou indivíduos que usam o sistema | — |
| Sistema de software | Nível mais alto: "something that delivers value to its users, whether they are human or not" | Domínios de produto, bounded contexts, capacidades, feature teams, tribos e squads normalmente não são sistemas |
| Contêiner | "Not Docker!": aplicação ou armazenamento de dados que precisa estar rodando; "a runtime boundary around some code that is being executed or some data that is being stored" | JARs, DLLs e módulos normalmente não são contêineres; SPA entregue por servidor = 2 contêineres; S3/RDS controlado pelo time = contêineres |
| Componente | "a grouping of related functionality encapsulated behind a well-defined interface"; não implantável separadamente; todos os componentes de um contêiner rodam no mesmo processo | Empacotamento é preocupação ortogonal |
| Código | Classes, interfaces, enums, funções que implementam um componente | — |

## Diagramas e "recomendado?"

Regra geral ([diagrams](https://c4model.com/diagrams)): "you don't need to use all 4 levels of diagram; only those that add value - the system context and container diagrams are sufficient for most software development teams."

| Diagrama | Escopo | Elementos primários / de apoio | Recomendado? (literal) |
|---|---|---|---|
| System context | Um sistema | o sistema / pessoas e sistemas ligados | "Yes, a system context diagram is recommended for all software development teams." |
| Container | Um sistema | contêineres / pessoas e sistemas ligados a eles | "Yes, a container diagram is recommended for all software development teams." |
| Component | Um contêiner | componentes / contêineres, pessoas e sistemas ligados | "No, only create component diagrams if you feel they add value, and consider automating their creation for long-lived documentation." |
| Code | Um componente | elementos de código | "No, particularly for long-lived documentation because most IDEs can generate this level of detail on demand." |
| System landscape | Empresa/organização/departamento | pessoas e sistemas do escopo ("really just a system context diagram without a specific focus") | "Yes, particularly for larger organisations - it's a bridge into the enterprise architecture world." |
| Dynamic | Uma feature/caso de uso | elementos interagindo em runtime; interações numeradas | "No, dynamic diagrams should be used sparingly to show interesting/recurring patterns or features that require a complicated set of interactions." |
| Deployment | Sistema(s) em **um** ambiente | nós, instâncias de sistema e contêiner / nós de infraestrutura | "Yes." |

O diagrama de contêineres "says very little about deployment aspects such as clustering, load balancers, replication, failover, etc"; isso vai para o diagrama de implantação, um por ambiente (ícones de provedor são permitidos se constarem na legenda).

## Notação ([notation](https://c4model.com/diagrams/notation))

O C4 é "notation independent". Regras literais:
- "Every diagram should have a title describing the diagram type and scope (e.g. 'System Context diagram for My Software System')."
- "Every diagram should have a key/legend explaining the notation being used (e.g. shapes, colours, border styles, line types, arrow heads, etc)."
- "Acronyms and abbreviations (business/domain or technology) should be understandable by all audiences, or explained in the diagram key/legend."
- "The type of every element should be explicitly specified (e.g. Person, Software System, Container or Component)."
- "Every element should have a short description, to provide an 'at a glance' view of key responsibilities."
- "Every container and component should have a technology explicitly specified."
- "Every line should represent a unidirectional relationship."
- "Every line should be labelled, the label being consistent with the direction and intent of the relationship (e.g. dependency or data flow). Try to be as specific as possible with the label, ideally avoiding single words like, 'Uses'."
- "Relationships between containers (typically these represent inter-process communication) should have a technology/protocol explicitly labelled."
- Cores: "you are free to use whatever colours you like! Just make sure that any colour coding is consistent (within and across diagrams) and be careful of things like black and white printers, color blindness, etc."

## Checklist de revisão (21 perguntas; [checklist](https://c4model.com/diagrams/checklist))

Todas as perguntas são de resposta sim/não (que todas devam ser "sim" é a leitura desta skill).
- **Geral:** título? tipo do diagrama claro? escopo claro? legenda?
- **Elementos:** todo elemento tem nome? tipo (nível de abstração) claro? sabe-se o que faz? tecnologias claras, quando aplicável? acrônimos/abreviações, cores, formas, ícones, estilos de borda e tamanhos de elemento compreensíveis?
- **Relações:** toda seta rotulada com a intenção? descrição bate com a direção? tecnologias/protocolos claros, quando aplicável? acrônimos, cores, pontas de seta e estilos de linha compreensíveis?

## Escalar e limites ([FAQ](https://c4model.com/faq))

- Sistema grande: dividir em vários diagramas simples no mesmo nível, cada um com um foco (área de negócio, bounded context, caso de uso...), em vez de um diagrama sobrecarregado.
- O C4 não cobre processos de negócio, workflows, máquinas de estado, modelos de domínio e de dados; complementar com BPMN, UML, ER etc.
- Menos adequado a firmware embarcado e a soluções de customização pesada (SAP, Salesforce).
- Com arc42: Context and Scope = System Context; Building Block View nível 1 = Container; nível 2 = Component; nível 3 = Code. O diagrama de implantação não é mapeado pelo FAQ; usá-lo na seção 7 do arc42 é aproximação desta skill.

## Complementos do livro (Simon Brown, *The C4 model for visualising software architecture*, Leanpub, 2022; paráfrase)

- **Obrigatório vs. opcional:** todo sistema deve ter contexto (cap. 6) e contêineres (cap. 7). Componentes são opcionais para documentação duradoura (esforço de manter; poluição visual com mais de um punhado de componentes); em geral não se desenha para armazenamento de dados nem contêineres muito simples. Código: opcional, em geral não recomendado.
- **Microsserviços e serverless:** os que o time não controla = sistemas externos; os que o time possui = contêineres, e seus armazenamentos são outros contêineres; funções serverless (Lambda, Functions) = contêineres, por serem implantáveis separadamente.
- **Evite "módulo" e "subsistema"** (difícil mapear para a base real); frameworks e bibliotecas são escolhas de tecnologia de componentes, não componentes.
- **Atributos de qualidade:** podem entrar como texto na descrição do elemento ou na seta (volume, latência-alvo); segurança e outras preocupações transversais ficam melhor em documentação complementar; replicação e clustering, no diagrama de implantação.
- **Vocabulário:** se a organização já tem um, mantenha-o desde que explicitamente definido; a hierarquia de abstração é o que importa.
