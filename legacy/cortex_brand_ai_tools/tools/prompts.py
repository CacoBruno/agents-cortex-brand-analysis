

system_autor = ''' Extraia  da notícia o autor da publicação. O autor da notícia é quem escreveu ou assina a notícia. Nunca alguém que é personagem da notícia"
        Se o autor for o nome do jornal ou 'redação', retorne 'Não assinada'. Sem não encortrar, retorne 'Não assinada'. Sempre retorne um nome próprio com as primeiras letra em caixa alta (ex. Claudia Bogossian). 
        Se não houver encontrado um nome próprio, retorne "Não assinada"'''

system_news = ''' Extraia da notícia o título, o conteúdo, o autor da publicação e a data da publicação.
                O autor da notícia é quem escreveu ou assina a notícia. Nunca alguém que é personagem da notícia"
                Se o autor for o nome do jornal ou 'redação', retorne 'Não assinada'. Sem não encortrar, retorne 'Não assinada'. Sempre retorne um nome próprio com as primeiras letra em caixa alta (ex. Claudia Bogossian). 
                Se não houver encontrado um nome próprio, retorne "Não assinada"
                Não crie informações quando não encontrado
                
                '''

system_download = ''' Extraia as informações nencessárias para fazer o download na plataforma.
                As informações são:
                Extrai das informações do cliente o 'link original', 'link', titulo, id_analise_midia, assunto_especifico.
    
    Recebe as informações do cliente e retorna as informações em uma lista de dicionário
    'link_original' refere-se às variáveis do campo da plataforma 'Link original da publicação'. É um link de notícias ou de redes sociais Ex. ['https://www.otempo.com.br/carnaval/2025/2025/2/27/maquiagens-de-carnaval-veja-tendencias-e-dicas-para-fazer-a-producao-durar-ate-o-fim-da-folia', 'https://www.cnnbrasil.com.br/economia/macroeconomia/tiktok-pode-gerar-r-39-bi-em-mercadorias-e-ser-concorrente-do-e-commerce','https://www.instagram.com/reel/DGgcEGHyoYz/', 'https://cultura.uol.com.br/beleza/noticias/2025/02/26/240_carnaval-2025-aposte-no-brilho-e-monte-sua-make-com-glitter.html']," \
    'link' refere-se às variáveis do campo da plataforma 'Link', que são os links das clipadoras. Não pode ser link de notícias.  Ex. ['https://nome_cliente.empauta.com/e6/noticia/2502181739860178001?autolog=eJwzMDA3MrMwNAeSBkYGRqYGRoYWACpABAM--3D', 'https://nome_cliente.empauta.com/e6/noticia/2502091739104790012?autolog=eJwzMDA3MrMwNAeSBkYGRqZAwhIAKj8EAw--3D--3D', 'https://nome_cliente.empauta.com/e6/noticia/2502171739835719018?autolog=eJwzMDA3MrMwNAeSBkYGRqYGRoYWACpABAM--3D', 'https://visualizacao.boxnet.com.br/#/?t=0005714A7C346E4383703FC93899783402000000018BD7E70488CF3403D9CCC36A5BBDCE326C231E275C23090A7E9469C92F8AB2EF7B25DE7206B6E5FA72517E343C33C6631A96077D9A4018C1A749AAD99F37749D935C27E8DB0C118031A3D5705CE277', 'https://visualizacao.boxnet.com.br/#/?t=0005714A7C346E4383703FC938997834020000000F604F355C7A1E180D2AC051F185FC6AFC62CAD2734881A583645C80F09C95C079FBBC41C502960338F961ECF6A7BF8C451D64B825F57CB091FB844BB046586CADD307047F0AFA1151163CA0924B11B3']," \
    'titulo' refere-se às variáveis do campo da plataforma 'Título' Ex. ['Natura mantém tratativas com IG4 visando venda da Avon fora da América Latina', 'Maquiagens de Carnaval: Veja tendências e dicas para fazer a produção durar até o fim da folia', 'Carnaval 2025: aposte no brilho e monte sua make com glitter', 'Ceará mira capitalizar Castelão e mais 46 equipamentos no Estado', 'Conheça os 10 homens mais ricos do mundo em 2025']," \
    'id_analise_midia' refere-se às variáveis do campo da plataforma 'Chave Análise de Mídia Hash'. É um hash, sempre com 32 caracteres e sem sentido lógico Ex. ['00177260292d105c722ad91c83f242ba','002bff019239b414a70df7b759c0c487', '002d8ff7cc098f97eb86801d7695833d','00307ae6a81467a7427cc9558cf4a4de', '0035bfea76c2add93be4f0582cabb506', '003d67a6bff6d28c6011e3f7c634deeb']," \
    'assunto_especifico' refere-se às variáveis do campo da plataforma 'Assunto específico'. Ex. ['Prêmios e Rankings', 'Lançamento de produto', 'Reviews e Indicações de produto']"]        
    'Empresa analisada' -> a variável é uma string e sempre vai ser o nome da empresa analisada na matéria ex. ['Grupo Boticário', 'Natura', 'Itaú', 'Bradesco', etc.]"
    'Produto analisado' -> a variável é uma string e sempre vai ser o nome de um produto analisado na matéria ex. ['Heineken', 'Eisenbahn', 'Devassa', etc.]"
    
         # Atenção:
        Preciso que retorne todas as variáves e as informações que não identificar pode retornar como vazia []
        Não crie informações quando não encontrado e só insira no dicionário as informações que estão no prompt. Não crie!
                
                '''


system_change_variable = ''' 

     Extraia as variáveis que devem ser mudada.
     
     As informações são:
            
     
            link_original -> 'é o link original da publicação. É a url das notícias de sites e/ou url de posts de redes socais, como Instagram, YouTube e Facebook. ATENÇÃO: Não pode ter link da clipadora que tem 'empauta' ou 'boxnet'. Ex. 'https://www.otempo.com.br/carnaval/2025/2025/2/27/maquiagens-de-carnaval-veja-tendencias-e-dicas-para-fazer-a-producao-durar-ate-o-fim-da-folia', 'https://www.cnnbrasil.com.br/economia/macroeconomia/tiktok-pode-gerar-r-39-bi-em-mercadorias-e-ser-concorrente-do-e-commerce','https://www.instagram.com/reel/DGgcEGHyoYz/', 'https://cultura.uol.com.br/beleza/noticias/2025/02/26/240_carnaval-2025-aposte-no-brilho-e-monte-sua-make-com-glitter.html'"           "'link_clipadora' refere-se às variáveis do campo da plataforma 'link_clipadora', que são os links das clipadoras. Precisa ter 'empauta' ou 'boxnet' na string. Se não tiver, não pode considerado Ex. 'https://nome_cliente.empauta.com/e6/noticia/2502181739860178001?autolog=eJwzMDA3MrMwNAeSBkYGRqYGRoYWACpABAM--3D', 'https://nome_cliente.empauta.com/e6/noticia/2502091739104790012?autolog=eJwzMDA3MrMwNAeSBkYGRqZAwhIAKj8EAw--3D--3D', 'https://nome_cliente.empauta.com/e6/noticia/2502171739835719018?autolog=eJwzMDA3MrMwNAeSBkYGRqYGRoYWACpABAM--3D', 'https://visualizacao.boxnet.com.br/#/?t=0005714A7C346E4383703FC93899783402000000018BD7E70488CF3403D9CCC36A5BBDCE326C231E275C23090A7E9469C92F8AB2EF7B25DE7206B6E5FA72517E343C33C6631A96077D9A4018C1A749AAD99F37749D935C27E8DB0C118031A3D5705CE277', 'https://visualizacao.boxnet.com.br/#/?t=0005714A7C346E4383703FC938997834020000000F604F355C7A1E180D2AC051F185FC6AFC62CAD2734881A583645C80F09C95C079FBBC41C502960338F961ECF6A7BF8C451D64B825F57CB091FB844BB046586CADD307047F0AFA1151163CA0924B11B3'"
            'link_clipadora -> Field(description="São urls referentes as clipadoras. A url sempre vai ter 'empauta' ou 'boxnet' na sua string. ATENÇÂO: Não entram url de sites de notícias Ex. 'https://nome_cliente.empauta.com/e6/noticia/2502181739860178001?autolog=eJwzMDA3MrMwNAeSBkYGRqYGRoYWACpABAM--3D', 'https://nome_cliente.empauta.com/e6/noticia/2502091739104790012?autolog=eJwzMDA3MrMwNAeSBkYGRqZAwhIAKj8EAw--3D--3D', 'https://nome_cliente.empauta.com/e6/noticia/2502171739835719018?autolog=eJwzMDA3MrMwNAeSBkYGRqYGRoYWACpABAM--3D', 'https://visualizacao.boxnet.com.br/#/?t=0005714A7C346E4383703FC93899783402000000018BD7E70488CF3403D9CCC36A5BBDCE326C231E275C23090A7E9469C92F8AB2EF7B25DE7206B6E5FA72517E343C33C6631A96077D9A4018C1A749AAD99F37749D935C27E8DB0C118031A3D5705CE277', 'https://visualizacao.boxnet.com.br/#/?t=0005714A7C346E4383703FC938997834020000000F604F355C7A1E180D2AC051F185FC6AFC62CAD2734881A583645C80F09C95C079FBBC41C502960338F961ECF6A7BF8C451D64B825F57CB091FB844BB046586CADD307047F0AFA1151163CA0924B11B3'
            'titulo' refere-se às variáveis do campo da plataforma 'Título' Ex. ['Natura mantém tratativas com IG4 visando venda da Avon fora da América Latina', 'Maquiagens de Carnaval: Veja tendências e dicas para fazer a produção durar até o fim da folia', 'Carnaval 2025: aposte no brilho e monte sua make com glitter', 'Ceará mira capitalizar Castelão e mais 46 equipamentos no Estado', 'Conheça os 10 homens mais ricos do mundo em 2025']," \
            'id_analise_midia' refere-se às variáveis do campo da plataforma 'Chave Análise de Mídia Hash'. É um hash, sempre com 32 caracteres e sem sentido lógico Ex. ['00177260292d105c722ad91c83f242ba','002bff019239b414a70df7b759c0c487', '002d8ff7cc098f97eb86801d7695833d','00307ae6a81467a7427cc9558cf4a4de', '0035bfea76c2add93be4f0582cabb506', '003d67a6bff6d28c6011e3f7c634deeb'],"  \            


            'Alcance total' ->  a variável é um interger e não é uma lista fechada ex. [56764, 1788, 1167, 906320],  
            'Tier' ->, a variável é uma string e sempre vai ser: 'Tier 1', 'Tier 2', 'Tier 3' ou 'Outros', 
            'Empresa analisada' -> a variável é uma string e sempre vai ser o nome da empresa analisada na matéria ex. ['Grupo Boticário', 'Natura', 'Itaú', 'Bradesco', etc.]
            'Produto analisado' -> a variável é uma string e sempre vai ser o nome de um produto analisado na matéria ex. ['Heineken', 'Eisenbahn', 'Devassa', etc.]
            'Sentimento' ->  a variável é uma string e será sempre as três labels e só podem ser estas: 'Positivo', 'Negativo' e 'Neutro'
            'Nível de Protagonismo final' ->  a variável é uma string e será sempre as seguintes labels e só podem ser estas: 'Citação relevante', 'Figurante', 'Protagonismo', 'Referencia contextual / Setor'   
            'Tópico' -> a variável é uma string, sendo uma única palavra que sumariza a matéria. ex.['Sustentabilidade', 'Institucional', 'Inovação', 'Empresa empregadora'], 
            'Assunto específico' -> a variável é uma string, sendo uma frase pequena que resume a presença da marca na matéria ex. ['Prêmios e Rankings', 'Lançamento de produto', 'Reviews e Indicações de produto'],
            'Ação' ->  a variável é uma string, sendo uma frase curta que explica a ação de comunicação da empresa. ex. ['O Boticário - Perfumaria Masculia', 'Itaú - Show da Madonna', 'Heineken - Lolapalloza'] 
            'Origem da Menção' -> a variável é uma string, sendo que sempre vai ser e somente ser 'Espontânea' ou 'Trabalhada' 
            'Jornalista' -> a variável é uma string. É o nome do autor da reportagem ou publicação analisada. ex. ['Mauro Cezar Perreira', 'Guilherme Amado', 'Juliana Del Piva'], 
            'Temas' -> a variável é uma string, sendo uma única palavra que sumariza a matéria. ex.['Sustentabilidade', 'Institucional', 'Inovação', 'Empresa empregadora'] 


        # Atenção:
        Preciso que retorne todas as variáves e as informações que não identificar pode retornar como vazia ''
        NUNCA crie informações quando não encontrado!!! 
        Só insira no dicionário as informações que estão no prompt. Não invente!

'''




ex_prompt_review = '''  


        a matéria é 017e8965db86eaac055adb69022d37ec
        e o sentimento é neutro e o assunto específico é A Cortex tem a melhor IA do mercado

        a segunda matéria 01e85dc3c387bb007ba6f930466c534e
        é protagonista e origem da menção é Espontânea

        a terceita matéria é 02011dea4c0e6b198e93b52864e4c981
        jornalsta é Claudia Bogossian


'''