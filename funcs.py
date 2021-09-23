import hashlib
import requests
import pandas as pd
from lxml import html
from datetime import datetime, timedelta, date
from fake_useragent import UserAgent
import json
from math import ceil
import os
import itertools


class CrawlerClass:

    ano_atual = datetime.today().year
    hj = date.today()
    dias_3 = hj - timedelta(days=3)

    # Faz um POST com os parametros da API no site da camara e recebe um json com a resposta
    # Passa como parametros :
    # * o ano_atual => como há recesso parlamentar no final do ano, nao ha riscos de perder propostas nos 3 primeiros dias do ano
    # * o tipo de proposicao (PL, PLP ou PEC)
    # * o numero da pagina => a api exporta cum conunto de dados limitados por pagina

    def acessa_api_camara(self, ano_atual, tipo_proposicao, n_i):
        ua = UserAgent()
        url = "https://www.camara.leg.br/api/v1/busca/proposicoes/_search"
        payload = {
            "order": "data",
            "ano": ano_atual,
            "pagina": n_i,
            "tiposDeProposicao": tipo_proposicao
        }
        headers = {
            'Content-Type': "application/json",
            'User-Agent': ua.random
            }
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        return response.json()

    # ================================================================================

    # Chama a função acessa_api_camara() e recebe o json com os dados das proposicoes
    # Busca a quantidade total de paginas com proposicoes e aloca na variavel qtd_pags
    # Busca a ultima data da primeira pag. Caso seja mais do que os 3 dias, retorna uam lista da funcao retorna_props()
    # Caso seja menos do que 2 dias, vai pora a pagina seguinte e faz a mesma busca até que a data seja maior que 3 dias,
    # fazerndo um break e retornando a lista da funcao retorna_props()

    def limita_props_dos_3_ultimos_dias(self, tipo_proposicao):
        ano_atual = CrawlerClass.ano_atual
        dias_3 = CrawlerClass.dias_3
        n_i = 1
        resp_json = self.acessa_api_camara(ano_atual, tipo_proposicao, n_i)
        qtd_total = resp_json['aggregations']['ano']['buckets'][0]['doc_count']
        qtd = len(resp_json['hits']['hits'])
        qtd_pags = ceil(qtd_total / qtd)
        datau = resp_json['hits']['hits'][(qtd-1)]['_source']['dataApresentacao'][:10]
        datau = datetime.strptime(datau, '%Y-%m-%d').date()
        if datau >= dias_3:
            lista_preposicoes = []
            while n_i < qtd_pags:
                print(f'== Fazendo o crawling da pagina {n_i}')
                resp_json = self.acessa_api_camara(ano_atual, tipo_proposicao, n_i)
                n_i += 1
                qtd_paginado = len(resp_json['hits']['hits'])
                rr = self.retorna_props(qtd_paginado, resp_json, dias_3)
                if rr == []:
                    break
                lista_preposicoes.append(rr)
            return list(itertools.chain.from_iterable(lista_preposicoes))
        else:
            print(f'== Fazendo o crawling da pagina {n_i}')
            return self.retorna_props(qtd, resp_json, dias_3)

    # ================================================================================

    # Recece a resposta em JSON da API da Camara e extrair dados (data, nome da proposicao e id)
    # A Id da proposição é usada para completar o link do pdf de Inteiro Teor
    # cada pd é salvo e extraído o hash md5
    # Com isso, o md5 de cada proposicao é formando listas com (data, nome da proposicao,  id e md5)
    # A função retorna uma listas com essas listas

    def retorna_props(self, qtd, resp_json, dias_3):
        print('Fazendo scraping dos dados.')
        lista_preps = []
        i = 0
        while i < qtd:
            data = resp_json['hits']['hits'][i]['_source']['dataApresentacao'][:10]
            data = datetime.strptime(data, '%Y-%m-%d').date()
            titulo = resp_json['hits']['hits'][i]['_source']['titulo']
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
                    print(f'Data: {data.strftime("%Y-%m-%d")} - Proposicao: {titulo} - md5: {md5_pdf}')
                lista_preps.append([data.strftime('%Y-%m-%d'), titulo, id_preposicao, md5_pdf])
            else:
                pass

        return lista_preps

    # ================================================================================

    # Exportando o dataframe
    # Remove o pdf usado para fazer o hash md5 da pasta
    # Monta e retorna um dataframe com a lista recebida

    def exporta_dataframe(self, tipo_proposicao):
        try:
            salva_pdf = 'salva_pdf'
            path = f'{salva_pdf}.pdf'
            os.remove(path)
        except:
            pass
        try:
            sigalei = self.limita_props_dos_3_ultimos_dias(tipo_proposicao)
            df = pd.DataFrame(sigalei, columns = ['data', 'projeto', 'index_projeto', 'md5'])
        except:
            sigalei = self.limita_props_dos_3_ultimos_dias(tipo_proposicao)
            loop = len(sigalei)
            x = 0
            df_list = []
            while x < loop:
                df_loop = pd.DataFrame(sigalei[x], columns = ['data', 'projeto', 'index_projeto', 'md5'])
                df_list.append(df_loop)
                x += 1
            df = pd.concat(df_list)
        return df

    # ================================================================================

    # Salvando em CSV

    def salva_csv(self, df, p):
        return df.to_csv(f'{p}.csv', index=False, sep=';')

    # ================================================================================

    # Salva o dataframe em JSON

    def salva_json(self, df, p):
        retorno_json = df.to_json(orient='records')
        with open(f'{p}.json', 'w') as f:
            json.dump(json.loads(retorno_json), f)

    # ============================================================================
    # =============================== || TESTES || ===============================
    # ============================================================================

    def limita_props_dos_3_ultimos_dias_para_teste(self, tipo_proposicao):
        ano_atual = CrawlerClass.ano_atual
        dias_3 = CrawlerClass.dias_3
        n_i = 1
        resp_json = self.acessa_api_camara(ano_atual, tipo_proposicao, n_i)
        qtd_total = resp_json['aggregations']['ano']['buckets'][0]['doc_count']
        qtd = len(resp_json['hits']['hits'])
        qtd_pags = ceil(qtd_total / qtd)
        datau = resp_json['hits']['hits'][(qtd - 1)]['_source']['dataApresentacao'][:10]
        datau = datetime.strptime(datau, '%Y-%m-%d').date()
        if datau >= dias_3:
            lista_preposicoes = []
            while n_i < qtd_pags:
                resp_json = self.acessa_api_camara(ano_atual, tipo_proposicao, n_i)
                n_i += 1
                qtd_paginado = len(resp_json['hits']['hits'])
                rr = self.retorna_props_para_teste(qtd_paginado, resp_json, dias_3)
                if rr == []:
                    break
                lista_preposicoes.append(rr)
            return list(itertools.chain.from_iterable(lista_preposicoes))
        else:
            return self.retorna_props_para_teste(qtd, resp_json, dias_3)


    def retorna_props_para_teste(self, qtd, resp_json, dias_3):
        lista_preps = []
        i = 0
        while i < qtd:
            data = resp_json['hits']['hits'][i]['_source']['dataApresentacao'][:10]
            data = datetime.strptime(data, '%Y-%m-%d').date()
            id_preposicao = resp_json['hits']['hits'][i]['_id']
            i += 1
            if data >= dias_3:
                lista_preps.append(id_preposicao)
            else:
                pass
        lista_preps = [int(i) for i in lista_preps]
        return lista_preps

    def retorna_lista_da_api_dos_dados_abertos_teste(self, tipo_proposicao):
        ano_atual = CrawlerClass.ano_atual
        dias_3 = CrawlerClass.dias_3
        url = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes?siglaTipo={tipo_proposicao}&ano={ano_atual}&dataApresentacaoInicio={dias_3.year}-{'{:02d}'.format(dias_3.month)}-{'{:02d}'.format(dias_3.day)}&itens=1000&ordem=DESC&ordenarPor=id"
        response = requests.get(url).json()['dados']
        t = len(response)
        lista_id_props_api = []
        i = 0
        while i < t:
            id_p = response[i]['id']
            i += 1
            lista_id_props_api.append(id_p)
        return lista_id_props_api

    def baixa_pdf_e_faz_hash_md5_para_teste(self):
        url_prep = 'https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao=2299267'
        resp = requests.get(url=url_prep)
        tree = html.fromstring(html=resp.text)
        link_pdf = tree.xpath('//*[@id="content"]/h3[1]/span[2]/a/@href')[0]
        elo = link_pdf[link_pdf.find('codteor'):]
        url_pdf = f'https://www.camara.leg.br/proposicoesWeb/prop_mostrarintegra?{elo}.pdf'
        chunk_size = 2000
        r = requests.get(url_pdf, stream=True)
        salva_pdf = 'tests/mockproposicao_id_2299267_baixada_para_teste.pdf'
        with open(salva_pdf, 'wb') as fd:
            for chunk in r.iter_content(chunk_size):
                fd.write(chunk)
        path = salva_pdf
        with open(path, 'rb') as opened_file:
            content = opened_file.read()
            md5 = hashlib.md5()
            md5.update(content)
            md5_pdf = md5.hexdigest()
        try:
            path = salva_pdf
            os.remove(path)
        except:
            pass
        return md5_pdf

    def moch_pdf_faz_hash_md5_para_teste(self):
        path = r'tests/mock/mock_PL-3213-2021.pdf'
        with open(path, 'rb') as opened_file:
            content = opened_file.read()
            md5 = hashlib.md5()
            md5.update(content)
            return md5.hexdigest()
