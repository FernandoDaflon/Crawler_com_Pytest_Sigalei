import funcs

sigalei = funcs.CrawlerClass()

def test_acesso_a_api_do_site_da_camara():
    lista_proposicoes = ['PL', 'PLP', 'PEC']
    for proposicao in lista_proposicoes:
        test_response = sigalei.acessa_api_camara('2021', proposicao, 1)
        response_proposicao = test_response['hits']['hits'][0]['_source']['titulo'][:3]
        assert proposicao == (response_proposicao).strip()

def test_de_match_da_api_dos_dados_abertos_com_api_dentro_do_dite_da_camara():
    lista_proposicoes = ['PL', 'PLP', 'PEC']
    for proposicao in lista_proposicoes:
        test_lista_id_props_api_do_site_camara_ = sigalei.limita_props_dos_3_ultimos_dias_para_teste(proposicao)
        test_list_lista_id_props_api_dados_abertos = sigalei.retorna_lista_da_api_dos_dados_abertos_teste(proposicao)
        assert set(sorted(test_lista_id_props_api_do_site_camara_)) == set(sorted(test_list_lista_id_props_api_dados_abertos))

def test_de_match_de_hash_md5_entre_pdf_Inteiro_teor_baixado_e_mock():
    hash_md5_pdf_Inteiro_teor_baixado = sigalei.baixa_pdf_e_faz_hash_md5_para_teste()
    hash_md5_pdf_Inteiro_teor_mockado = sigalei.moch_pdf_faz_hash_md5_para_teste()
    assert hash_md5_pdf_Inteiro_teor_baixado == hash_md5_pdf_Inteiro_teor_mockado

