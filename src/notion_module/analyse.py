def from_interventions_to_datas(interventions):
    datas = []
    for intervention in interventions:
        data = {
            'Ville': intervention['properties']['Ville']['select']['name'] if intervention['properties']['Ville'][
                'select'] else None,
            'Ecole': intervention['properties']['Ecole']['select']['name'] if intervention['properties']['Ecole'][
                'select'] else None,
            'Classe': intervention['properties']['Classe']['select']['name'] if intervention['properties']['Classe'][
                'select'] else None,
            'Nombre heures': intervention['properties']['Nombre heures']['number'],
            'Tarif horaire': intervention['properties']['Tarif horaire']['number'],
            'Facturé': intervention['properties']['Facturé']['checkbox'],
            'Date de début': intervention['properties']['Date de début']['date']['start'] if
            intervention['properties']['Date de début']['date'] else None,
        }

        datas.append(data)

    return datas