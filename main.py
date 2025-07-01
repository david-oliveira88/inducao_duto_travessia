from duto import solo, duto, coordenadas, cabo, linha_transmissao

if __name__ == "__main__":

    solo1 = solo(resistividade=100)

    # Coordenadas do duto
    coordenadas_duto = coordenadas(x=0, y=0)

    duto1 = duto(diametro=0.3, solo=solo1, espessura_cobertura=0.003, coordenadas=coordenadas_duto)

    # Cabos da linha de transmissão
    cabo1 = cabo(coordenadas=coordenadas(x=10, y=20), corrente=100)
    cabo2 = cabo(coordenadas=coordenadas(x=15, y=25), corrente=150)
    cabo3 = cabo(coordenadas=coordenadas(x=20, y=30), corrente=200)

    # Linha de transmissão
    lt = linha_transmissao(cabos=[cabo1, cabo2, cabo3], solo=solo1)

    # Imprimir características e impedâncias mútuas
    duto1.imprimir_caracteristicas(lt)
