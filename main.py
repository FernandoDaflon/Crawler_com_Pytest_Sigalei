import funcs
import os
import logging


def main(tipo_proposicao):
    df_sigalei = funcs.CrawlerClass()
    df = df_sigalei.exporta_dataframe(tipo_proposicao)
    try:
        os.remove('salva_pdf.pdf')
    except:
        pass
    formato_exportacao = input('DIGITE O FORMATO PARA SER EXPORTADO (CSV OU JSON): ').upper().strip()
    lista_formatos = ['CSV', 'JSON']
    while formato_exportacao not in lista_formatos:
        print('')
        print(f'==> {formato_exportacao} NAO E UM DOS DISPONIVEIS')
        formato_exportacao = input("==> DIGITE CSV OU JSON: ").upper().strip()
    if formato_exportacao == 'CSV':
        df_sigalei.salva_csv(df, tipo_proposicao)
    elif formato_exportacao == 'JSON':
        df_sigalei.salva_json(df, tipo_proposicao)
    else:
        print('FORMATO NAO DISPONIVEL')



if __name__ == '__main__':
    logging.warning('Iniciando')
    lista_proposicoes = ['PL', 'PLP', 'PEC']
    tipo_proposicao = input("DIGITE A PROPOSICAO (PL, PLP ou PEC): ").upper().strip()
    while tipo_proposicao not in lista_proposicoes:
        print('')
        print(f'==> {tipo_proposicao} NAO E UMA DAS PROPOSICOES DISPONIVEIS')
        tipo_proposicao = input("==> DIGITE UMA DAS SEGUINTES PROPOSICOES (PL, PLP ou PEC): ").upper().strip()
    main(tipo_proposicao)
    logging.warning('Fim')




















#
# def main(tipo_proposicao):
#     df_sigalei = funcs.CrawlerClass()
#     df = df_sigalei.exporta_dataframe(tipo_proposicao)
#     try:
#         os.remove('salva_pdf.pdf')
#     except:
#         pass
#     formato_exportacao = input('DIGITE O FORMATO PARA SER EXPORTADO (CSV OU JSON): ').upper().strip()
#     if formato_exportacao == 'CSV':
#         df_sigalei.salva_csv(df, tipo_proposicao)
#     elif formato_exportacao == 'JSON':
#         df_sigalei.salva_json(df, tipo_proposicao)
#     else:
#         print('FORMATO NAO DISPONIVEL')
#
#
# if __name__ == '__main__':
#     logging.warning('Iniciando')
#     main(input("DIGITE A PROPOSICAO (PL, PLP ou PEC): ").upper().strip())
#     logging.warning('Fim')
