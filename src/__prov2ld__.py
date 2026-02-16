import json
import sys
from typing import Dict, List, Any
import argparse

class ProvJsonToJsonldConverter:
    PROV_JSONLD_CONTEXT = "https://openprovenance.org/prov-jsonld/context.json"
    
    # Mapping of PROV-JSON categories to PROV-JSONLD types
    TYPE_MAPPINGS = {
        'entity': 'prov:Entity',
        'activity': 'prov:Activity',
        'agent': 'prov:Agent',
        'wasGeneratedBy': 'prov:Generation',
        'used': 'prov:Usage',
        'wasInformedBy': 'prov:Communication',
        'wasStartedBy': 'prov:Start',
        'wasEndedBy': 'prov:End',
        'wasInvalidatedBy': 'prov:Invalidation',
        'wasDerivedFrom': 'prov:Derivation',
        'wasAttributedTo': 'prov:Attribution',
        'wasAssociatedWith': 'prov:Association',
        'actedOnBehalfOf': 'prov:Delegation',
        'wasInfluencedBy': 'prov:Influence',
        'specializationOf': 'provext:Specialization',
        'alternateOf': 'provext:Alternate',
        'hadMember': 'provext:Membership'
    }
    
    # Relation properties mapping from PROV-JSON keys to PROV-JSONLD keys
    RELATION_PROPERTIES = {
        'wasGeneratedBy': {'prov:entity': 'entity', 'prov:activity': 'activity', 'prov:time': 'time'},
        'used': {'prov:entity': 'entity', 'prov:activity': 'activity', 'prov:time': 'time'},
        'wasInformedBy': {'prov:informed': 'informed', 'prov:informant': 'informant'},
        'wasStartedBy': {'prov:activity': 'activity', 'prov:trigger': 'trigger', 'prov:starter': 'starter', 'prov:time': 'time'},
        'wasEndedBy': {'prov:activity': 'activity', 'prov:trigger': 'trigger', 'prov:ender': 'ender', 'prov:time': 'time'},
        'wasInvalidatedBy': {'prov:entity': 'entity', 'prov:activity': 'activity', 'prov:time': 'time'},
        'wasDerivedFrom': {'prov:generatedEntity': 'generatedEntity', 'prov:usedEntity': 'usedEntity', 'prov:activity': 'activity', 'prov:generation': 'generation', 'prov:usage': 'usage'},
        'wasAttributedTo': {'prov:entity': 'entity', 'prov:agent': 'agent'},
        'wasAssociatedWith': {'prov:activity': 'activity', 'prov:agent': 'agent', 'prov:plan': 'plan'},
        'actedOnBehalfOf': {'prov:delegate': 'delegate', 'prov:responsible': 'responsible', 'prov:activity': 'activity'},
        'wasInfluencedBy': {'prov:influencee': 'influencee', 'prov:influencer': 'influencer'},
        'specializationOf': {'prov:specificEntity': 'specificEntity', 'prov:generalEntity': 'generalEntity'},
        'alternateOf': {'prov:alternate1': 'alternate1', 'prov:alternate2': 'alternate2'},
        'hadMember': {'prov:collection': 'collection', 'prov:entity': 'entity'}
    }
    
    def __init__(self):
        self.namespaces = {}
        
    def convert(self, prov_json: Dict[str, Any]) -> Dict[str, Any]:
        self.namespaces = self._extract_namespaces(prov_json)
        
        context = self._build_context()
        
        graph = []
        if 'bundle' in prov_json:
            for bundle_id, bundle_content in prov_json['bundle'].items():
                bundle_obj = self._convert_bundle(bundle_id, bundle_content)
                graph.append(bundle_obj)
        
        for category, type_name in self.TYPE_MAPPINGS.items():
            if category in prov_json:
                statements = self._convert_category(category, prov_json[category], type_name)
                graph.extend(statements)
        
        result = {"@context": context, "@graph": graph}
        
        return result
    
    def _extract_namespaces(self, prov_json: Dict[str, Any]) -> Dict[str, str]:
        namespaces = {}
        if 'prefix' in prov_json:
            namespaces = dict(prov_json['prefix'])
        return namespaces
    
    def _build_context(self) -> List[Any]:
        context = []
        if self.namespaces:
            context.append(self.namespaces)
        context.append(self.PROV_JSONLD_CONTEXT)
        return context
    
    def _convert_category(self, category: str, items: Dict[str, Any], type_name: str) -> List[Dict[str, Any]]:
        result = []
        
        for item_id, item_data in items.items():
            obj = self._convert_item(item_id, item_data, type_name, category)
            result.append(obj)
        
        return result
    
    def _convert_item(self, item_id: str, item_data: Dict[str, Any], type_name: str, category: str) -> Dict[str, Any]:
        obj = {"@type": type_name, "@id": item_id}
        
        if category in self.RELATION_PROPERTIES:
            obj = self._convert_relation(item_id, item_data, type_name, category)
        else:
            obj = self._convert_element(item_id, item_data, type_name)
        
        return obj
    
    def _convert_element(self, item_id: str, item_data: Dict[str, Any], type_name: str) -> Dict[str, Any]:
        obj = {"@type": type_name, "@id": item_id}
        
        for key, value in item_data.items():
            if key == 'prov:type':
                obj['prov:type'] = self._convert_value(value)
            elif key == 'prov:label':
                obj['prov:label'] = self._convert_label(value)
            elif key == 'prov:location':
                obj['prov:location'] = self._convert_value(value)
            elif key == 'prov:value':
                obj['prov:value'] = self._convert_value(value)
            elif key.startswith('prov:'):
                obj[key] = self._convert_value(value)
            elif ':' in key:  # Custom attribute with namespace
                obj[key] = self._convert_value(value)
        
        if type_name == 'prov:Activity':
            if 'prov:startTime' in item_data:
                obj['startTime'] = item_data['prov:startTime']
            if 'prov:endTime' in item_data:
                obj['endTime'] = item_data['prov:endTime']
        
        return obj
    
    def _convert_relation(self, item_id: str, item_data: Dict[str, Any], type_name: str, category: str) -> Dict[str, Any]:
        obj = {"@type": type_name}
        
        # Add ID only if present and not a generic placeholder
        if item_id and not item_id.startswith('_:'):
            obj["@id"] = item_id
        elif item_id and item_id.startswith('_:'):
            # Keep blank node identifiers
            obj["@id"] = item_id
        
        # Map relation-specific properties
        property_map = self.RELATION_PROPERTIES.get(category, {})
        
        for prov_key, jsonld_key in property_map.items():
            if prov_key in item_data:
                obj[jsonld_key] = item_data[prov_key]
        
        for key, value in item_data.items():
            if key in property_map:
                continue
                
            if key == 'prov:type':
                obj['prov:type'] = self._convert_value(value)
            elif key == 'prov:label':
                obj['prov:label'] = self._convert_label(value)
            elif key == 'prov:location':
                obj['prov:location'] = self._convert_value(value)
            elif key == 'prov:role':
                obj['prov:role'] = self._convert_value(value)
            elif key.startswith('prov:'):
                obj[key] = self._convert_value(value)
            elif ':' in key:  # Custom attribute
                obj[key] = self._convert_value(value)
        
        return obj
    
    def _convert_value(self, value: Any) -> List[Dict[str, Any]]:
        if not isinstance(value, list):
            value = [value]
        
        result = []
        for item in value:
            if isinstance(item, dict):
                if '$' in item or 'type' in item:
                    converted = {}
                    if '$' in item:
                        converted['@value'] = item['$']
                    if 'type' in item:
                        converted['@type'] = item['type']
                    if 'lang' in item:
                        converted['@language'] = item['lang']
                    result.append(converted)
                else:
                    result.append(item)
            else:
                result.append({"@value": str(item)})
        
        return result
    
    def _convert_label(self, value: Any) -> List[Dict[str, Any]]:
        if not isinstance(value, list):
            value = [value]
        
        result = []
        for item in value:
            if isinstance(item, dict):
                label_obj = {"@value": item.get('$', '')}
                if 'lang' in item:
                    label_obj['@language'] = item['lang']
                result.append(label_obj)
            else:
                result.append({"@value": str(item)})
        
        return result
    
    def _convert_bundle(self, bundle_id: str, bundle_data: Dict[str, Any]) -> Dict[str, Any]:
        bundle_namespaces = {}
        if 'prefix' in bundle_data:
            bundle_namespaces = dict(bundle_data['prefix'])
        
        bundle_context = []
        if bundle_namespaces:
            bundle_context.append(bundle_namespaces)
        bundle_context.append(self.PROV_JSONLD_CONTEXT)
        
        graph = []
        for category, type_name in self.TYPE_MAPPINGS.items():
            if category in bundle_data:
                statements = self._convert_category(category, bundle_data[category], type_name)
                graph.extend(statements)
        
        bundle_obj = {
            "@type": "prov:Bundle",
            "@id": bundle_id,
            "@context": bundle_context,
            "@graph": graph
        }
        
        return bundle_obj


def main():
    parser = argparse.ArgumentParser(
        description='Convert PROV-JSON to PROV-JSONLD format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument('input', type=str, help='Input PROV-JSON file (or stdin if not provided)')
    parser.add_argument('output', type=str, help='Output PROV-JSONLD file (or stdout if not provided)')
    
    args = parser.parse_args()
    
    with open(args.input, 'r', encoding='utf-8') as f:
        prov_json = json.load(f)
    
    converter = ProvJsonToJsonldConverter()
    prov_jsonld = converter.convert(prov_json)
        
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(prov_jsonld, f, ensure_ascii=False)
    print(f"Converted PROV-JSON to PROV-JSONLD: {args.output}")


if __name__ == '__main__':
    main()
