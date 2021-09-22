# Crawler_com_Pytest_Sigalei
### Programa em Python com crawler que retorna csv ou json com md5 dos PDFs de Inteiro Teor dos últimos 3 dias do site da câmara e faz testes

***
## Explicação do Projeto

* __PROBLEMA__ :arrow_right: Conferir se os documentos de *Inteiro Teor* das proposições (*PEC, PLP ou PL*) mais recentes foram baixados corretamente nos últimos três dias.
* __SOLUÇÃO__ :arrow_right: Sistema que receba o tipo de proposição desejada (*PEC, PLP ou PL*) e retorne uma lista de hash MD5 gerada a partir dos documentos de Inteiro Teor das proposições apresentadas nos últimos três dias na Câmara dos Deputados. Essa hash é utilizada para verificar se aquele documento já foi baixado ou não.

***

## Como executar o projeto:

Crie um ambiente virtual:

```
virtualenv -p python.exe env
env\Scripts\activate.bat
```

Depois instale as *libs* do projeto:

```
pip freeze > requirements.txt
```

Com o ambiente virtual ativado e com as *libs* instaladas digite no terminal `  python main.py  `

<pre>
(env) E:\SIGALEI>python main.py
WARNING:root:Iniciando
DIGITE A PROPOSICAO (PL. PLP ou PEC): <b>INSIRA AQUI A PROPOSICAO QUE DESEJA PESQUISAR</b> (pode ser minúsculo)
DIGITE O FORMATO PARA SER EXPORTADO (CSV OU JSON): <b>INSIRA AQUI O FORMATO DE SAIDA</b> (pode ser minúsculo)
WARNING:root:Fim
</pre>

:arrow_right: Como resultado, um arquivo __CSV__ ou __JSON__ será salvo na pasta com o nome da proposição escolhida.

***
## Explicando o Crawler:

1) No site oficial da [Câmara dos Deputados](https://www.camara.leg.br/busca-portal/proposicoes/pesquisa-simplificada) uma __API__ é consumida para retornar um *dicionário* com a resposta referente aos parâmetros passados.

## * acessa_api_camara()

Faz um __POST__ com os parâmetros da API (__*order, ano, pagina, tiposDeProposicao*__) no site da Câmara e recebe um __JSON de resposta__.

A url que passamos os parâmetros é: ` https://www.camara.leg.br/api/v1/busca/proposicoes/_search `

Passa como parâmetros do *payload*:

* o ano_atual → como há recesso parlamentar no final do ano, não há riscos de perder propostas nos 3 primeiros dias do ano.
* o tipo de proposição → *PL, PLP ou PEC*.
* o número da página → a __API__ exporta cum conjunto de dados limitados por pagina, com isso, passamos o número de cada página.
* a string "data" → para ordenar a resposta pela *data* mais recente.

Passa como parâmetros do *headers*:

* application/json → informando o Content-Type
* um user agent → da *lib fake-useragent*. O método *random* passa *user-agents* de forma aleatória (google, firefox, IE, Safari ...)

```
def acessa_api_camara(ano_atual, tipo_proposicao, numero_da_pagina):
    ua = UserAgent()
    url = "https://www.camara.leg.br/api/v1/busca/proposicoes/_search"
    payload = {
        "order":"data",
        "ano":ano_atual,
        "pagina":numero_da_pagina,
        "tiposDeProposicao": tipo_proposicao
    }
    headers = {
        'Content-Type': "application/json",
        'User-Agent': ua.random    
        }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()
```
***
2) Com a resposta da __API__ do site oficial da Câmara dos Deputados é feito o *scrape* da __*data da apresentação da proposição*__, do __*título*__(ou nome)__*da proposição*__ e __*id da proposição*__. 
   <br></br>
   O id da proposição é passado no link de cada proposição `  f'https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={id_preposicao}'  `
   <br></br>
   É feito um request nesse link e no __html__ de resposta encontramos o link do nosso documento alvo, o __PDF de Inteiro Teor__. 
   <br></br>
   O download do __PDF de Inteiro Teor__ é feito em um arquivo temporário e é extraído o hash MD5 desse arquivo. 
   <br></br>
   Uma lista é retornada. 

## * retorna_props()

Recebe a resposta em __JSON__ da __API__ da Câmara e extrai dados **data de apresentação, titulo da proposição e id da proposição**.

Ex.:

data de apresentação | titulo da proposição | id da proposição
-- | -- | --
2021-09-17T15:25:00 | PL 3211/2021 | 2299232

A *Id da proposição* é usada para completar o link onde está localizado o PDF de __*Inteiro Teor*__ e fazer o download.
Cada pd é salvo temporariamente e desse arquivo temporário é extraído o hash md5.

Com isso, o md5 de cada proposição é formando listas com **data de apresentação, título da proposição, id da proposição e md5**.

Ex.:

data de apresentação | titulo da proposição | id da proposição | md5
-- | -- | -- | --
2021-09-17 | PL 3211-2021 | 2299232 | 4d9eef77f177f4e9b4113f9163b575e5

A função retorna uma lista com essas listas.

```
def retorna_props(qtd, resp_json, dias_3):
    lista_preps = []
    i = 0
    while i < qtd:
        data = resp_json['hits']['hits'][i]['_source']['dataApresentacao'][:10]
        data = datetime.strptime(data, '%Y-%m-%d').date()
        titulo = resp_json['hits']['hits'][i]['_source']['titulo'].replace('/','-')
        id_preposicao = resp_json['hits']['hits'][i]['_id']
        i += 1
        if data >= dias_3:
            url_prep = f'https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={id_preposicao}'
            resp = requests.get(url=url_prep)
            tree = html.fromstring(html=resp.text)
            link_pdf = tree.xpath('//*[@id="content"]/h3[1]/span[2]/a/@href')[0]
            elo = link_pdf[link_pdf.find('codteor'):]
            url_pdf = f'https://www.camara.leg.br/proposicoesWeb/prop_mostrarintegra?{elo}.pdf'
            chunk_size = 2000
            r = requests.get(url_pdf, stream=True)
            salva_pdf = 'salva_pdf'
            with open(f'{salva_pdf}.pdf', 'wb') as fd:
                for chunk in r.iter_content(chunk_size):
                    fd.write(chunk)
            path = f'{salva_pdf}.pdf'
            with open(path, 'rb') as opened_file:
                content = opened_file.read()
                md5 = hashlib.md5()
                md5.update(content)
                md5_pdf = md5.hexdigest()          
            lista_preps.append([data.strftime('%Y-%m-%d'), titulo, id_preposicao, md5_pdf])
        else:
            pass
    
    return lista_preps
```
***
3) A lista que recebemos precisa conter todas as proposições dos ultimos __3 dias__, mas nem sempre essa lista está contida apenas na primeira página que o crawler faz o *scrape*.
<br></br>
É retornado uma lista com listas de todas as proposições dos últimos 3 dias de todas as páginas.


## * limita_props_dos_3_ultimos_dias()

Chama a função __acessa_api_camara()__ e recebe o __json com os dados das proposições__.

Busca a quantidade total de páginas com proposições e aloca na variável *qtd_pags*.

Busca a última data da primeira página. Caso seja mais do que os 3 dias, retorna uma lista da __funcao retorna_props()__

Caso seja menos do que 2 dias, vai para a página seguinte e faz a mesma busca até que a data seja maior que 3 dias,
fazendo um break e retornando a lista da função __retorna_props()__

```
def limita_props_dos_3_ultimos_dias(tipo_proposicao):    
    n_i = 1
    resp_json = acessa_api_camara(ano_atual, tipo_proposicao, n_i)
    qtd_total = resp_json['aggregations']['ano']['buckets'][0]['doc_count']
    qtd = len(resp_json['hits']['hits'])
    qtd_pags = ceil(qtd_total / qtd)
    datau = resp_json['hits']['hits'][(qtd-1)]['_source']['dataApresentacao'][:10]
    datau = datetime.strptime(datau, '%Y-%m-%d').date()
    if datau >= dias_3:
        lista_preposicoes = []
        while n_i < qtd_pags:        
            resp_json = acessa_api_camara(ano_atual, tipo_proposicao, n_i)
            n_i += 1
            qtd_paginado = len(resp_json['hits']['hits'])
            rr = retorna_props(qtd_paginado, resp_json, dias_3)
            if rr == []:
                break        
            lista_preposicoes.append(rr)
        return list(itertools.chain.from_iterable(lista_preposicoes))
    else:
        return retorna_props(qtd, resp_json, dias_3)
```
***
4) A lista de listas é convertida em um *DataFrame*.
<br></br>
Um *DataFrame Pandas* é retornado.

## * exporta_dataframe()

Exporta um dataframe para o tipo de proposição *PL, PLP ou PEC*.

Remove o pdf usado para fazer o hash md5 da pasta.

Monta e retorna um *DataFrame* com a lista recebida.

```
def exporta_dataframe(tipo_proposicao):
    try:
        salva_pdf = 'salva_pdf'
        path = f'{salva_pdf}.pdf'        
        os.remove(path)
    except:
        pass
    try:
        sigalei = limita_props_dos_3_ultimos_dias(tipo_proposicao)        
        df = pd.DataFrame(sigalei, columns = ['DATA', 'PROJETO', 'INDEX_PROJETO', 'MD5'])
    except:    
        sigalei = limita_props_dos_3_ultimos_dias(tipo_proposicao)
        loop = len(sigalei)
        print(len)
        x = 0
        df_list = []
        while x < loop:
            df_loop = pd.DataFrame(sigalei[x], columns = ['DATA', 'PROJETO', 'INDEX_PROJETO', 'MD5'])
            df_list.append(df_loop)
            x +=1
        df = pd.concat(df_list)
    return df    
```
***
5) Salva o *DataFrame* em __CSV__.

## * salva_csv()

Salva o dataframe em CSV

```
def salva_csv(df, p):
    return df.to_csv(f'{p}.csv', index=False, sep=';')
```


6) Salva o *DataFrame* em __JSON__.

## * salva_json()

Salva o *DataFrame* em JSON

```
def salva_json(df, p):    
    retorno_json = df.to_json(orient='records')
    with open(f'{p}.json', 'w') as f:
        json.dump(json.loads(retorno_json) , f)
```
***
## Como executar os testes automatizados:

Digite ` pytest -vv ` no terminal:

<pre>
(env) E:\SIGALEI><b>pytest -vv</b>
</pre>

O *pytest* irá rodas os testes programados em seguida e apresentar se cada teste passou (__PASSED__) ou falhou (__FAILED__)

## Explicando os Testes:

Foram desenvolvidos 3 testes automatizados
***
1) Testando a resposta da API do site da Câmara.

## * test_acesso_a_api_do_site_da_camara()

   Uma lista com [*PL, PLP ou PEC*] é varrida testando cada uma das proposições.
   
   Cada proposição é passada como parâmetro da função *acessa_api_camara()*
   
   Caso a resposta esteja correta, é extraído o nome da proposição da resposta __JSON__ que recebemos.
   
   É realizado um *assert* comparando a proposição que foi passada como parâmetro e a proposição extraída da resposta. 
   
   Caso sejam iguais, o teste passou (__PASSED__)
   
   ```
   def test_acesso_a_api_do_site_da_camara():
    lista_proposicoes = ['PL', 'PLP', 'PEC']
    for proposicao in lista_proposicoes:
        test_response = sigalei.acessa_api_camara('2021', proposicao, 1)
        response_proposicao = test_response['hits']['hits'][0]['_source']['titulo'][:3]
        assert proposicao == (response_proposicao).strip()
   ```
   ***
2) Testando se a reposta dos últimos 3 dias da __API__ *dentro do site da Câmara* é a mesma obtida pela __API__ do *Dados Abertos* 

## * test_de_match_da_api_dos_dados_abertos_com_api_dentro_do_dite_da_camara()

Uma lista com [*PL, PLP ou PEC*] é varrida testando cada uma das proposições.
   
Cada proposição é passada como parâmetro das funções *limita_props_dos_3_ultimos_dias_para_teste()* & *retorna_lista_da_api_dos_dados_abertos_teste()*

Essas funções buscam as ids das proposições dos últimos 3 dias tanto na __API__ *dentro do site da Câmara* quanto __API__ do *Dados Abertos* 

É realizado um *assert* comparando as 2 listas de forma ordenada

Ex.:

`[2299492, 2299490, 2299463, 2299442] = [2299492, 2299490, 2299463, 2299442]`

Se as 2 listas foram iguais, o teste passou (__PASSED__)

```
def test_de_match_da_api_dos_dados_abertos_com_api_dentro_do_dite_da_camara():
    lista_proposicoes = ['PL', 'PLP', 'PEC']
    for proposicao in lista_proposicoes:
        test_lista_id_props_api_do_site_camara_ = sigalei.limita_props_dos_3_ultimos_dias_para_teste(proposicao)
        test_list_lista_id_props_api_dados_abertos = sigalei.retorna_lista_da_api_dos_dados_abertos_teste(proposicao)
        assert set(sorted(test_lista_id_props_api_do_site_camara_)) == set(sorted(test_list_lista_id_props_api_dados_abertos))
   ```
   ***
3) Testando hash md5 do PDF de Inteiro Teor baixado do site da Câmara

## * test_de_match_de_hash_md5_entre_pdf_Inteiro_teor_baixado_e_mock()

O arquivo PDF da *PL-3213-2021* foi baixado manualmente e salvo como __*mock_PL-3213-2021.pdf*__.

A função *moch_pdf_faz_hash_md5_para_teste()* fas o hash md5 desse arquivo.

A mesma proposição é baixada do link do site da Câmara e salvo temporariamente como __PDF__

A função *baixa_pdf_e_faz_hash_md5_para_teste()* faz o hash md5 do arquivo e o exclui em seguida.

É realizado um *assert* comparando os 2 hashs md5.

Ex.:

`f4bee1db1c5f08b1f9f25b57520d56d3 = f4bee1db1c5f08b1f9f25b57520d56d3`

Se as 2 hashs md5 foram iguais, o teste passou (__PASSED__)

```
def test_de_match_de_hash_md5_entre_pdf_Inteiro_teor_baixado_e_mock():
    hash_md5_pdf_Inteiro_teor_baixado = sigalei.baixa_pdf_e_faz_hash_md5_para_teste()
    hash_md5_pdf_Inteiro_teor_mockado = sigalei.moch_pdf_faz_hash_md5_para_teste()
    assert hash_md5_pdf_Inteiro_teor_baixado == hash_md5_pdf_Inteiro_teor_mockado
```
