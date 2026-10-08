key_words = [
    'Facebook', 'facebook', 'FACEBOOK', 'Facebok', 'facebok', 'FACEBOK',
    'Twitter', 'twitter', 'TWITTER', 'Twiter', 'twiter',
    'Instagram', 'instagram', 'INSTAGRAM',
    'TikTok', 'tiktok', 'TIKTOK', 'Tik Tok', 'tik tok', 'TIK TOK',
    'LinkedIn', 'linkedin', 'LINKEDIN', 'WhatsAp',
    'WhatsApp', 'whatsapp', 'WHATSAPP', 'Linkedin',
    'Whatsap', 'whatsap', 'WHATSAAP', 'Whatapp', 'whatapp', 'WHATAPP',
    'Whatasap', 'whatasap', 'WHATASAPP',
    'Whats', 'whats', 'WHAT',
    'Insta', 'insta', 'INSTA', 'Inst', 'inst', 'INST',
    'Snapchat', 'snapchat', 'SNAPCHAT', 'Snap', 'snap', 'SNAP',
    'Pinterest', 'pinterest', 'PINTEREST', 'Pin', 'pin', 'PIN',
    'Reddit', 'reddit', 'REDDIT', 'Red', 'red', 'RED', 'Foto', 'Pixabay',
    'pixabay', 'SÃO PAULO', 'Reuters', 'São Paulo', 'Bloomberg Línea', 'Bloomberg'
]

company_names = ['Shein', 'AliExpress', 'Sinerlog', 'Shopee', 'Americanascom',
                 'Mercado Livre', 'RAmericanas', 'CPFL']

specific_words = ['não', 'diz', 'ja', 'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro', 
'segunda-feira', 'semana', 'mês', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo', 'feira', 'leia', 'sobe', 'desce', 'update']


def get_leia_mais_terms():
    """List of terms that indicate links to other news, collected from vehicle studies

    Returns:
        [str]: Collection of terms in pattern format for use in regex
    """
    return 'Mais lidas|MAIS LIDAS|Mais Lidas|\
    Mais resultados|Mais Resultados|MAIS RESULTADOS|\
    Post Anterior|POST ANTERIOR|Post anterior|Post Anterior|\
    Fonte:|FONTE:|\
    Próximo Post|PRÓXIMO POST|Próximo post|\
    Podcasts|PODCASTS|\
    Veja também|VEJA TAMBÉM|Veja Também|\
    Saiba mais|SAIBA MAIS|Saiba Mais|\
    Leia mais|LEIA MAIS|Leia Mais|\
    Leia mais em:|LEIA MAIS EM:|Leia Mais Em:|\
    Ler mais|LER MAIS|Ler Mais|\
    Ver mais|VER MAIS|Ver Mais|\
    Tudo sobre|Tudo Sobre|TUDO SOBRE|\
    Últimas Notícias|ÚLTIMAS NOTÍCIAS|Últimas notícias|\
    Navegação de Post|NAVEGAÇÃO DE POST|Navegação de post|\
    Leia Também|Leia também|LEIA TAMBÉM|\
    Continue lendo|CONTINUE LENDO|Continue Lendo|\
    Artigo anterior|ARTIGO ANTERIOR|Artigo Anterior|\
    Próximo artigo|PRÓXIMO ARTIGO|Próximo Artigo|\
    Posts Recentes|POSTS RECENTES|Posts recentes|\
    Artigos mais recentes|ARTIGOS MAIS RECENTES|Artigos mais Recentes|Artigos Mais Recentes|\
    Mais lidas|+ Lidas|+ LIDAS|MAIS LIDAS|Mais Lidas|\
    ►|>>|>  >|>   >|Mais Recentes|Mais recentes|\
    Relacionados Posts|Posts relacionados|POSTS RELACIONADOS|Posts Relacionados|\
    Postagem anterior|POSTAGEM ANTERIOR|Postagem Anterior|\
    Destaque do dia|Destaque do Dia|DESTAQUE DO DIA|DestaqueS do dia|Destaques do Dia|DESTAQUES DO DIA|\
    Notícias que podem te interessar|NOTÍCIAS QUE PODEM TE INTERESSAR|\
    Notícias recentes|NOTÍCIAS RECENTES|Notícias Recentes|\
    Notícias relacionadas|NOTÍCIAS RELACIONADAS|\
    Mais sobre|MAIS SOBRE|Mais Sobre|\
    Mais do autor|MAIS DO AUTOR|Mais do Autor|Relacionados|\
    Artigos relacionados|ARTIGOS RELACIONADOS|Artigos Relacionados|PRÓXIMO|ANTERIOR|\
    Pela web|PELA WEB|Pela Web|\
    Outras notícias|OUTRAS NOTÍCIAS|Outras Notícias|\
    Últimas postagens|ÚLTIMAS POSTAGENS|Últimas Postagens|\
    Previous post|PREVIOUS POST|Previous Post|\
    Next post|NEXT POST|Next Post|\
    Read previous|READ PREVIOUS|Read Previous|\
    Read next|READ NEXT|\
    See more|SEE MORE|\
    Similar to|SIMILAR TO|\
    Popular now|POULAR NOW|\
    Just for you|JUST FOR YOU|\
    Mais histórias|MAIS HISTÓRIAS|\
    Edições anteriores|EDIÇÕES ANTERIORES|\
    Última edição|ÚLTIMA EDIÇÃO|\
    Postagens mais visitadas|POSTAGENS MAIS VISITADAS|\
    Principais notícias|PRINCIPAIS NOTÍCIAS|\
    Você pode gostar também|VOCÊ PODE GOSTAR TAMBÉM|\
    Está todo mundo clicando|ESTÁ TODO MUNDO CLICANDO|\
    Most Popular|MOST POPULAR|\
    Hot news|HOT NEWS|\
    Mais falados|MAIS FALADOS|\
    Veja mais|VEJA MAIS|Veja Mais|\
    Destaques da semana|DESTAQUES DA SEMANA|Destaques da Semana|\
    Notícia anterior|NOTÍCIA ANTERIOR|Notícia Anterior|\
    Proxima notícia|PRÓXIMA NOTÍCIA|Próxima Notícia|\
    É provável que você também goste|Talvez se interesse por|Sugestões para você|Acompanhe as novidades|CONTEÚDOS RELACIONADOS|\
    Últimas notícias sobre:|Últimas do dia:|Radar:|Compartilhe esta publicação:|Post Relacionado|Anterior|Próximo|Concorrência:|Concorrência IEC:|As mais lidas da semana:|As mais lidas:\
    Classificação indicativa:|Compartilhe:|Compartilhar:|Saiba mais em:|Saiba como:'


specific_terms = [
    'um', 'uma', 'uns', 'umas', 'o', 'a', 'os', 'as', 'ao', 'à', 'às', 'sendo',
    'pelo', 'pela', 'pelos', 'pelas', 'um', 'uma', 'uns', 'umas', 'de',
    'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas', 'por', 'para',
    'com', 'sem', 'sob', 'sobre', 'ante', 'após', 'até', 'contra', 'entre',
    'perante', 'desde', 'através', 'durante', 'exceto', 'salvo', 'mediante',
    'sai', 'volta', 'atrás', 'devem', 'atrás', 'caderno', 'argolado',
    'conforme', 'consoante', 'segundo', 'semelhante', 'mais', 'menos', 'ainda',
    'também', 'já', 'até', 'logo', 'pois', 'porém', 'mas', 'no', 'entanto',
    'todavia', 'contudo', 'ainda', 'assim', 'porque', 'como', 'uma', 'uma',
    'com', 'que', 'quando', 'onde', 'quem', 'qual', 'quais', 'cujo', 'cuja',
    'cujos', 'cujas', 'isto', 'isso', 'aquilo', 'nada', 'algo', 'alguém',
    'nenhum', 'nenhuma', 'todo', 'toda', 'todos', 'todas', 'muito', 'muita',
    'muitos', 'muitas', 'vários', 'várias', 'alguns', 'algumas', 'certo','deu', 'dra'
    'certa', 'certos', 'certas', 'outro', 'outra', 'outros', 'outras', 'mesmo', 'puxado',
    'mesma', 'mesmos', 'mesmas', 'próprio', 'própria', 'próprios', 'próprias', 'brasil',
    'cada', 'muito', 'muita', 'muitos', 'muitas', 'bastante', 'bastantes',
    'pouco', 'pouca', 'poucos', 'poucas', 'tão', 'tanta', 'tantos', 'tantas',
    'quanto', 'quanta', 'quantos', 'quantas', 'tudo', 'todo', 'toda', 'todos',
    'todas', 'nada', 'nenhum', 'nenhuma', 'algum', 'alguma', 'alguns', 'algumas',
    'você', 'ele', 'ela', 'eles', 'elas', 'nós', 'vós', 'e', 'mas', 'ou', 'porque',
    'como', 'quando', 'onde', 'que', 'quem', 'cujo', 'cuja', 'cujos', 'cujas',
    'a', 'o', 'para', 'por', 'com', 'em', 'de', 'sem', 'sob', 'sobre', 'ante',
    'após', 'até', 'contra', 'entre', 'desde', 'através', 'durante', 'exceto',
    'puxado', 'play', 'store', 'fed', 'dois', 'impulsionada', 'mil',
    'perante', 'segundo', 'mediante', 'conforme', 'assim', 'então', 'aqui', 'ali',
    'aí', 'acolá', 'lá', 'onde', 'quando', 'logo', 'porém', 'mas', 'mais', 'menos', 'bnp',
    'apesar', 'também', 'ainda', 'sim', 'não', 'nem', 'ou', 'para', 'porque', 'quando',
    'se', 'senão', 'que', 'porque', 'para', 'como', 'se', 'ainda', 'seja', 'sejam', 
    'fazer', 'faça', 'feito', 'fazendo', 'fiz', 'fizemos', 'faz', 'fazia', 'são', 
    'sobre', 'essa', 'esse', 'estas', 'estes', 'essas', 'esses', 'outra', 'tudo', 
    'toda', 'tudo', 'sempre', 'quando', 'lugar', 'hora', 'dia', 'semana', 'mês', 
    'ano', 'dias', 'anos', 'coisa', 'coisas', 'ser', 'estar', 'estou', 'está', 
    'estamos', 'estão', 'estive', 'esteve', 'estivemos', 'estiveram', 'estava', 
    'estávamos', 'estavam', 'estivera', 'estivéramos', 'esteja', 'estejamos', '+',
    'estejam', 'estivesse', 'estivéssemos', 'estivessem', 'estiver', 'estivermos', 
    'estiverem', 'hei', 'há', 'houve', 'havemos', 'houveram', 'houvera', 'houvéramos', 
    'haja', 'hajamos', 'hajam', 'houvesse', 'houvéssemos', 'houvessem', 'houver', 
    'houvermos', 'houverem', 'houverei', 'houverá', 'houveremos', 'houverão', 'houveria', 
    'houveríamos', 'houveriam', 'sou', 'somos', 'são', 'era', 'éramos', 'eram', 'fui', 
    'foi', 'fomos', 'foram', 'fora', 'fôramos', 'seja', 'sejamos', 'sejam', 'fosse', 
    'fôssemos', 'fossem', 'for', 'formos', 'forem', 'serei', 'será', 'seremos', 'serão', 
    'sexta', 'nesta', 'aquela','funciona', 'parcelado',' apostar', 'pausa', 'avança', 'seguinte', 'quer', 'garantir', 
'fim', 'última',  'conv.', 'participar' 'região',    'seria', 'seríamos', 'seriam', 'tenho', 'tem', 'temos', 'têm', 'tinha', 'tínhamos', 
    'tinham', 'tive', 'teve', 'tivemos', 'tiveram', 'tivera', 'tivéramos', 'tenha', 
    'tenhamos', 'tenham', 'tivesse', 'tivéssemos', 'tivessem', 'tiver', 'tivermos', 
    'tiverem', 'terei', 'terá', 'teremos', 'terão', 'teria', 'teríamos', 'teriam',
    'é', 'vai', 'irá', 'i', 'vá', 'vou', 'irei', 'ir', 'iremos', 'pode', 'poder', 
    'podem', 'podes', 'poderá', 'poderia', 'poderiam', 'poderá', 'poderá', 'você',
    'ele', 'ela', 'eles', 'elas', 'nós', 'vós', 'sim', 'não', 'se', 'nada', 'algum',
    'qualquer', 'uns', 'umas', 'quantos', 'quantas', 'mesmo', 'mesma', 'mesmos', 
    'mesmas', 'todo', 'toda', 'todos', 'todas', 'cada', 'qualquer', 'algo', 'nenhum', 'maior', 'abre',
    'nenhuma', 'ambos', 'ambas', 'próprio', 'própria', 'próprios', 'próprias', 
    'outro', 'outra', 'outros', 'outras', 'certo', 'certa', 'certos', 'certas', 
    'diferente', 'diferentes', 'tão', 'tanta', 'tantos', 'tantas', 'quanto', 'quanta',
    'quantos', 'quantas', 'todo', 'toda', 'todos', 'todas', 'cada', 'cada', 'cada', 
    'cada', 'cada', 'cada', 'cada', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 
    'qual', 'qual', 'qual', 'qual', 'quais', 'quais', 'quais', 'quais', 'quais', 
    'quais', 'quais', 'quais', 'quais', 'quais', 'cujo', 'cujo', 'cujo', 'cujo', 
    'cuja', 'cuja', 'cuja', 'cuja', 'cujos', 'cujos', 'cujos', 'cujos', 'cujas', 
    'cujas', 'cujas', 'cujas', 'isto', 'isto', 'isto', 'isto', 'isso', 'isso', 
    'isso', 'isso', 'aquilo', 'aquilo', 'aquilo', 'aquilo', 'nada', 'nada', 'nada',
    'nada', 'algo', 'algo', 'algo', 'algo', 'alguém', 'alguém', 'alguém', 'alguém',
    'ninguém', 'ninguém', 'ninguém', 'ninguém', 'nenhum', 'nenhum', 'nenhum', 
    'nenhum', 'nenhuma', 'nenhuma', 'nenhuma', 'nenhuma', 'outro', 'outro', 'outro',
    'outro', 'outra', 'outra', 'outra', 'outra', 'outros', 'outros', 'outros', 
    'outros', 'outras', 'outras', 'outras', 'outras', 'meu', 'minha', 'meus', 'minhas',
    'teu', 'tua', 'teus', 'tuas', 'seu', 'sua', 'seus', 'suas', 'nosso', 'nossa', 
    'nossos', 'nossas', 'vosso', 'vossa', 'vossos', 'vossas', 'seu', 'sua', 'seus', 
    'suas', 'meu', 'teu', 'seu', 'nossa', 'vossa', 'minha', 'tua', 'sua', 'nossa', 
    'vossa', 'minha', 'tua', 'sua', 'nossa', 'vossa', 'meu', 'teu', 'seu', 'nosso', 
    'vosso', 'meus', 'teus', 'seus', 'nossos', 'vossos', 'minhas', 'tuas', 'suas', 
    'nossas', 'vossas', 'meu', 'teu', 'seu', 'nosso', 'vosso', 'meus', 'teus', 'seus', 
    'nossos', 'vossos', 'minhas', 'tuas', 'suas', 'nossas', 'vossas', 'meu', 'teu', 
    'seu', 'nosso', 'vosso', 'meus', 'teus', 'seus', 'nossos', 'vossos', 'minhas', 
    'tuas', 'suas', 'nossas', 'vossas', 'este', 'esta', 'estes', 'estas', 'esse', 
    'essa', 'esses', 'essas', 'aquele', 'aquela', 'aqueles', 'aquelas', 'isto', 
    'isso', 'aquilo', 'meu', 'teu', 'seu', 'nosso', 'vosso', 'teus', 'meus', 
    'seus', 'nossos', 'vossos', 'minha', 'tua', 'sua', 'nossa', 'vossa', 
    'tuas', 'minhas', 'suas', 'nossas', 'vossas', 'aqui', 'ali', 'acolá', 
    'lá', 'onde', 'quando', 'logo', 'porém', 'mas', 'mais', 'menos', 
    'apesar', 'também', 'ainda', 'sim', 'não', 'nem', 'ou', 'para', 
    'porque', 'quando', 'se', 'senão', 'que', 'porque', 'para', 'como', 
    'se', 'ainda', 'seja', 'sejam', 'fazer', 'faça', 'feito', 'fazendo', 
    'fiz', 'fizemos', 'faz', 'fazia', 'são', 'sobre', 'essa', 'esse', 
    'estas', 'estes', 'essas', 'esses', 'outra', 'tudo', 'toda', 
    'tudo', 'sempre', 'quando', 'lugar', 'hora', 'dia', 'semana', 
    'mês', 'ano', 'dias', 'anos', 'coisa', 'coisas', 'ser', 'estar', 
    'estou', 'está', 'estamos', 'estão', 'estive', 'esteve', 'estivemos', 
    'estiveram', 'estava', 'estávamos', 'estavam', 'estivera', 'estivéramos', 
    'esteja', 'estejamos', 'estejam', 'estivesse', 'estivéssemos', 'estivessem', 
    'estiver', 'estivermos', 'estiverem', 'hei', 'há', 'houve', 'havemos', 
    'houveram', 'houvera', 'houvéramos', 'haja', 'hajamos', 'hajam', 'houvesse', 
    'houvéssemos', 'houvessem', 'houver', 'houvermos', 'houverem', 'houverei', 
    'houverá', 'houveremos', 'houverão', 'houveria', 'houveríamos', 'houveriam', 
    'sou', 'somos', 'são', 'era', 'éramos', 'eram', 'fui', 'foi', 'fomos', 'foram', 
    'fora', 'fôramos', 'seja', 'sejamos', 'sejam', 'fosse', 'fôssemos', 'fossem', 
    'for', 'formos', 'forem', 'serei', 'será', 'seremos', 'serão', 'seria', 'seríamos', 
    'seriam', 'tenho', 'tem', 'temos', 'têm', 'tinha', 'tínhamos', 'tinham', 'tive', 
    'teve', 'tivemos', 'tiveram', 'tivera', 'tivéramos', 'tenha', 'tenhamos', 'tenham', 
    'tivesse', 'tivéssemos', 'tivessem', 'tiver', 'tivermos', 'tiverem', 'terei', 'terá', 
    'teremos', 'terão', 'teria', 'teríamos', 'teriam', 'é', 'vai', 'irá', 'i', 'vá', 'vou', 
    'irei', 'ir', 'iremos', 'pode', 'poder', 'podem', 'podes', 'poderá', 'poderia', 'poderiam', 
    'poderá', 'poderá', 'você', 'ele', 'ela', 'eles', 'elas', 'nós', 'sim', 'não', 'se', 'nada', 
    'algum', 'qualquer', 'uns', 'umas', 'quantos', 'quantas', 'mesmo', 'mesma', 'mesmos', 'mesmas', 
    'todo', 'toda', 'todos', 'todas', 'cada', 'qualquer', 'algo', 'nenhum', 'nenhuma', 'ambos', 'ambas', 
    'próprio', 'própria', 'próprios', 'próprias', 'outro', 'outra', 'outros', 'outras', 'certo', 'certa', 
    'certos', 'certas', 'diferente', 'diferentes', 'tão', 'tanta', 'tantos', 'tantas', 'quanto', 'quanta', 
    'quantos', 'quantas', 'todo', 'toda', 'todos', 'todas', 'cada', 'cada', 'cada', 'cada', 'cada', 'cada', 
    'cada', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 'quais', 'quais', 
    'quais', 'quais', 'quais', 'quais', 'quais', 'quais', 'quais', 'quais', 'cujo', 'cujo', 'cujo', 'cujo', 
    'cuja', 'cuja', 'cuja', 'cuja', 'cujos', 'cujos', 'cujos', 'cujos', 'cujas', 'cujas', 'cujas', 'cujas', 
    'isto', 'isto', 'isto', 'isto', 'isso', 'isso', 'isso', 'isso', 'aquilo', 'aquilo', 'aquilo', 'aquilo', 
    'nada', 'nada', 'nada', 'nada', 'algo', 'algo', 'algo', 'algo', 'alguém', 'alguém', 'alguém', 'alguém', 
    'ninguém', 'ninguém', 'ninguém', 'ninguém', 'nenhum', 'nenhum', 'nenhum', 'nenhum', 'nenhuma', 'nenhuma', 
    'nenhuma', 'nenhuma', 'outro', 'outro', 'outro', 'outro', 'outra', 'outra', 'outra', 'outra', 'outros', 
    'outros', 'outros', 'outros', 'outras', 'outras', 'outras', 'outras', 'meu', 'minha', 'meus', 'minhas', 
    'teu', 'tua', 'teus', 'tuas', 'seu', 'sua', 'seus', 'suas', 'nosso', 'nossa', 'nossos', 'nossas', 'vosso', 
    'vossa', 'vossos', 'vossas', 'seu', 'sua', 'seus', 'suas', 'meu', 'teu', 'seu', 'nossa', 'vossa', 'minha', 
    'tua', 'sua', 'nossa', 'vossa', 'minha', 'tua', 'sua', 'nossa', 'vossa', 'meu', 'teu', 'seu', 'nosso', 
    'vosso', 'meus', 'teus', 'seus', 'nossos', 'vossos', 'minhas', 'tuas', 'suas', 'nossas', 'vossas', 'meu', 
    'teu', 'seu', 'nosso', 'vosso', 'meus', 'teus', 'seus', 'nossos', 'vossos', 'minhas', 'tuas', 'suas', 'nossas', 
    'vossas', 'meu', 'teu', 'seu', 'nosso', 'vosso', 'meus', 'teus', 'seus', 'nossos', 'vossos', 'minhas', 'tuas', 
    'suas', 'nossas', 'vossas', 'este', 'esta', 'estes', 'estas', 'esse', 'essa', 'esses', 'essas', 'aquele', 'aquela', 
    'aqueles', 'aquelas', 'isto', 'isso', 'aquilo', 'meu', 'teu', 'seu', 'nosso', 'vosso', 'teus', 'meus', 'seus', 
    'nossos', 'vossos', 'minha', 'tua', 'sua', 'nossa', 'vossa', 'tuas', 'minhas', 'suas', 'nossas', 'vossas', 
    'aqui', 'ali', 'acolá', 'lá', 'onde', 'quando', 'logo', 'porém', 'mas', 'mais', 'menos', 'apesar', 'também', 
    'ainda', 'sim', 'não', 'nem', 'ou', 'para', 'porque', 'quando', 'se', 'senão', 'que', 'porque', 'para', 'como', 
    'se', 'ainda', 'seja', 'sejam', 'fazer', 'faça', 'feito', 'fazendo', 'fiz', 'fizemos', 'faz', 'fazia', 'são', 
    'sobre', 'essa', 'esse', 'estas', 'estes', 'essas', 'esses', 'outra', 'tudo', 'toda', 'tudo', 'sempre', 'quando', 
    'lugar', 'hora', 'dia', 'semana', 'mês', 'ano', 'dias', 'anos', 'coisa', 'coisas', 'ser', 'estar', 'estou', 'está', 
    'estamos', 'estão', 'estive', 'esteve', 'estivemos', 'estiveram', 'estava', 'estávamos', 'estavam', 'estivera', 
    'estivéramos', 'esteja', 'estejamos', 'estejam', 'estivesse', 'estivéssemos', 'estivessem', 'estiver', 'estivermos', 
    'estiverem', 'hei', 'há', 'houve', 'havemos', 'houveram', 'houvera', 'houvéramos', 'haja', 'hajamos', 'hajam', 
    'houvesse', 'houvéssemos', 'houvessem', 'houver', 'houvermos', 'houverem', 'houverei', 'houverá', 'houveremos', 
    'houverão', 'houveria', 'houveríamos', 'houveriam', 'sou', 'somos', 'são', 'era', 'éramos', 'eram', 'fui', 'foi', 
    'fomos', 'foram', 'fora', 'fôramos', 'seja', 'sejamos', 'sejam', 'fosse', 'fôssemos', 'fossem', 'for', 'formos', 
    'forem', 'serei', 'será', 'seremos', 'serão', 'seria', 'seríamos', 'seriam', 'tenho', 'tem', 'temos', 'têm', 'tinha', 
    'tínhamos', 'tinham', 'tive', 'teve', 'tivemos', 'tiveram', 'tivera', 'tivéramos', 'tenha', 'tenhamos', 'tenham', 
    'tivesse', 'tivéssemos', 'tivessem', 'tiver', 'tivermos', 'tiverem', 'terei', 'terá', 'teremos', 'terão', 'teria', 
    'teríamos', 'teriam', 'é', 'vai', 'irá', 'i', 'vá', 'vou', 'irei', 'ir', 'iremos', 'pode', 'poder', 'podem', 
    'podes', 'poderá', 'poderia', 'poderiam', 'poderá', 'poderá', 'você', 'ele', 'ela', 'eles', 'elas', 'nós', 
    'sim', 'não', 'se', 'nada', 'algum', 'qualquer', 'uns', 'umas', 'quantos', 'quantas', 'mesmo', 'mesma', 
    'mesmos', 'mesmas', 'todo', 'toda', 'todos', 'todas', 'cada', 'qualquer', 'algo', 'nenhum', 'nenhuma', 
    'ambos', 'ambas', 'próprio', 'própria', 'próprios', 'próprias', 'outro', 'outra', 'outros', 'outras', 
    'certo', 'certa', 'certos', 'certas', 'diferente', 'diferentes', 'tão', 'tanta', 'tantos', 'tantas', 
    'quanto', 'quanta', 'quantos', 'quantas', 'todo', 'toda', 'todos', 'todas', 'cada', 'cada', 'cada', 'cada',
    'cada', 'cada', 'cada', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 
    'quais', 'quais', 'quais', 'quais', 'quais', 'quais', 'quais', 'quais', 'quais', 'quais', 'cujo', 'cujo', 
    'cujo', 'cujo', 'cuja', 'cuja', 'cuja', 'cuja', 'cujos', 'cujos', 'cujos', 'cujos', 'cujas', 'cujas', 'cujas', 
    'cujas', 'isto', 'isto', 'isto', 'isto', 'isso', 'isso', 'isso', 'isso', 'aquilo', 'aquilo', 'aquilo', 'aquilo', 
    'nada', 'nada', 'nada', 'nada', 'algo', 'algo', 'algo', 'algo', 'alguém', 'alguém', 'alguém', 'alguém', 'ninguém', 
    'ninguém', 'ninguém', 'ninguém', 'nenhum', 'nenhum', 'nenhum', 'nenhum', 'nenhuma', 'nenhuma', 'nenhuma', 'nenhuma', 
    'outro', 'outro', 'outro', 'outro', 'outra', 'outra', 'outra', 'outra', 'outros', 'outros', 'outros', 'outros', 
    'outras', 'outras', 'outras', 'outras', 'meu', 'minha', 'meus', 'minhas', 'teu', 'tua', 'teus', 'tuas', 'seu', 
    'sua', 'seus', 'suas', 'nosso', 'nossa', 'nossos', 'nossas', 'vosso', 'vossa', 'vossos', 'vossas', 'seu', 
    'sua', 'seus', 'suas', 'meu', 'teu', 'seu', 'nossa', 'vossa', 'minha', 'tua', 'sua', 'nossa', 'vossa', 
    'minha', 'tua', 'sua', 'nossa', 'vossa', 'meu', 'teu', 'seu', 'nosso', 'vosso', 'meus', 'teus', 'seus', 
    'nossos', 'vossos', 'minhas', 'tuas', 'suas', 'nossas', 'vossas', 'meu', 'teu', 'seu', 'nosso', 'vosso', 
    'meus', 'teus', 'seus', 'nossos', 'vossos', 'minhas', 'tuas', 'suas', 'nossas', 'vossas', 'meu', 'teu', 
    'seu', 'nosso', 'vosso', 'meus', 'teus', 'seus', 'nossos', 'vossos', 'minhas', 'tuas', 'suas', 'nossas', 
    'vossas', 'este', 'esta', 'estes', 'estas', 'esse', 'essa', 'esses', 'essas', 'aquele', 'aquela', 'aqueles', 
    'aquelas', 'isto', 'isso', 'aquilo', 'meu', 'teu', 'seu', 'nosso', 'vosso', 'teus', 'meus', 'seus', 'nossos', 
    'vossos', 'minha', 'tua', 'sua', 'nossa', 'vossa', 'tuas', 'minhas', 'suas', 'nossas', 'vossas', 'aqui', 
    'ali', 'acolá', 'lá', 'onde', 'quando', 'logo', 'porém', 'mas', 'mais', 'menos', 'apesar', 'também', 'ainda', 
    'sim', 'não', 'nem', 'ou', 'para', 'porque', 'quando', 'se', 'senão', 'que', 'porque', 'para', 'como', 'se', 
    'ainda', 'seja', 'sejam', 'fazer', 'faça', 'feito', 'fazendo', 'fiz', 'fizemos', 'faz', 'fazia', 'são', 'sobre', 
    'essa', 'esse', 'estas', 'estes', 'essas', 'esses', 'outra', 'tudo', 'toda', 'tudo', 'sempre', 'quando', 'lugar', 
    'hora', 'dia', 'semana', 'mês', 'ano', 'dias', 'anos', 'coisa', 'coisas', 'ser', 'estar', 'estou', 'está', 'estamos', 
    'estão', 'estive', 'esteve', 'estivemos', 'estiveram', 'estava', 'estávamos', 'estavam', 'estivera', 'estivéramos', 
    'esteja', 'estejamos', 'estejam', 'estivesse', 'estivéssemos', 'estivessem', 'estiver', 'estivermos', 'estiverem', 
    'hei', 'há', 'houve', 'havemos', 'houveram', 'houvera', 'houvéramos', 'haja', 'hajamos', 'hajam', 'houvesse', 
    'houvéssemos', 'houvessem', 'houver', 'houvermos', 'houverem', 'houverei', 'houverá', 'houveremos', 'houverão', 
    'houveria', 'houveríamos', 'houveriam', 'sou', 'somos', 'são', 'era', 'éramos', 'eram', 'fui', 'foi', 'fomos', 
    'foram', 'fora', 'fôramos', 'seja', 'sejamos', 'sejam', 'fosse', 'fôssemos', 'fossem', 'for', 'formos', 'forem', 
    'serei', 'será', 'seremos', 'serão', 'seria', 'seríamos', 'seriam', 'tenho', 'tem', 'temos', 'têm', 'tinha', 
    'tínhamos', 'tinham', 'tive', 'teve', 'tivemos', 'tiveram', 'tivera', 'tivéramos', 'tenha', 'tenhamos', 'tenham', 
    'tivesse', 'tivéssemos', 'tivessem', 'tiver', 'tivermos', 'tiverem', 'terei', 'terá', 'teremos', 'terão', 
    'teria', 'teríamos', 'teriam', 'é', 'vai', 'irá', 'i', 'vá', 'vou', 'irei', 'ir', 'iremos', 'pode', 
    'poder', 'podem', 'podes', 'poderá', 'poderia', 'poderiam', 'poderá', 'poderá', 'você', 'ele', 'ela', 
    'eles', 'elas', 'nós', 'sim', 'não', 'se', 'nada', 'algum', 'qualquer', 'uns', 'umas', 'quantos', 'quantas', 
    'mesmo', 'mesma', 'mesmos', 'mesmas', 'todo', 'toda', 'todos', 'todas', 'cada', 'qualquer', 'algo', 'nenhum', 
    'nenhuma', 'ambos', 'ambas', 'próprio', 'própria', 'próprios', 'próprias', 'outro', 'outra', 'outros', 'outras', 
    'certo', 'certa', 'certos', 'certas', 'diferente', 'diferentes', 'tão', 'tanta', 'tantos', 'tantas', 'quanto', 
    'quanta', 'quantos', 'quantas', 'todo', 'toda', 'todos', 'todas', 'cada', 'cada', 'cada', 'cada', 'cada', 'cada', 
    'cada', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 'qual', 'quais', 'quais', 'quais', 
    'quais', 'quais', 'quais', 'quais', 'quais', 'quais', 'quais', 'cujo', 'cujo', 'cujo', 'cujo', 'cuja', 'cuja', 
    'cuja', 'cuja', 'cujos', 'cujos', 'cujos', 'cujos', 'cujas', 'cujas', 'cujas', 'cujas', 'isto', 'isto', 'isto', 
    'isto', 'isso', 'isso', 'isso', 'isso', 'aquilo', 'aquilo', 'aquilo', 'aquilo', 'nada', 'nada', 'nada', 'nada', 
    'algo', 'algo', 'algo', 'algo', 'alguém', 'alguém', 'alguém', 'alguém', 'ninguém', 'ninguém', 'ninguém', 
    'ninguém', 'nenhum', 'nenhum', 'nenhum', 'nenhum', 'nenhuma', 'nenhuma', 'um',' dois', 'três',
    'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove', 'dez', 'tique', 'sextafeira', 'segundafeira', 'terçafeira',
    'quartafeira', 'quintafeira']