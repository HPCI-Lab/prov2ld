import json
import sys
from typing import Dict, List, Any, Optional, Tuple
import argparse
import subprocess

class ProvJsonldToGraphviz:
    # Shapes for different node types
    NODE_SHAPES = {
        'prov:Entity': 'ellipse',
        'prov:Activity': 'box',
        'prov:Agent': 'house'
    }
    
    # Colors for different node types
    NODE_COLORS = {
        'prov:Entity': '#FFFC87',      # Light yellow
        'prov:Activity': '#9FB1FC',     # Light blue
        'prov:Agent': '#FDB266'         # Light orange
    }
    
    # Edge styles for different relations
    EDGE_STYLES = {
        'prov:Generation': {'label': 'wasGeneratedBy', 'style': 'solid', 'dir': 'back', 'color': '#006400'},
        'prov:Usage': {'label': 'used', 'style': 'solid', 'dir': 'forward', 'color': '#8b0101'},
        'prov:Derivation': {'label': 'wasDerivedFrom', 'style': 'solid', 'dir': 'back'},
        'prov:Association': {'label': 'wasAssociatedWith', 'style': 'solid', 'dir': 'forward', 'color': '#fed37f'},  # dark yellow/goldenrod
        'prov:Attribution': {'label': 'wasAttributedTo', 'style': 'dashed', 'dir': 'back'},
        'prov:Communication': {'label': 'wasInformedBy', 'style': 'solid', 'dir': 'back'},
        'prov:Delegation': {'label': 'actedOnBehalfOf', 'style': 'dashed', 'dir': 'back'},
        'prov:Start': {'label': 'wasStartedBy', 'style': 'solid', 'dir': 'back'},
        'prov:End': {'label': 'wasEndedBy', 'style': 'solid', 'dir': 'back'},
        'prov:Invalidation': {'label': 'wasInvalidatedBy', 'style': 'solid', 'dir': 'back'},
        'prov:Influence': {'label': 'wasInfluencedBy', 'style': 'dotted', 'dir': 'back'},
        'provext:Specialization': {'label': 'specializationOf', 'style': 'solid', 'dir': 'back', 'arrowhead': 'onormal'},
        'provext:Alternate': {'label': 'alternateOf', 'style': 'dashed', 'dir': 'none'},
        'provext:Membership': {'label': 'hadMember', 'style': 'dotted', 'dir': 'forward'}
    }
    
    # Properties that represent references to other nodes
    REFERENCE_PROPERTIES = {
        'entity', 'activity', 'agent', 'generatedEntity', 'usedEntity',
        'informed', 'informant', 'trigger', 'starter', 'ender',
        'delegate', 'responsible', 'plan', 'influencee', 'influencer',
        'specificEntity', 'generalEntity', 'alternate1', 'alternate2',
        'collection', 'generation', 'usage'
    }
    
    def __init__(self, show_attributes: bool = True, direction: str = 'LR'):
        self.show_attributes = show_attributes
        self.show_relation_labels = True
        self.direction = direction
        self.nodes = {}
        self.edges = []
        self.namespaces = {}
        
    def convert(self, prov_jsonld: Dict[str, Any]) -> str:
        self._extract_namespaces(prov_jsonld.get('@context', []))
        
        graph = prov_jsonld.get('@graph', [])
        
        for item in graph:
            item_type = item.get('@type')
            
            if item_type in self.NODE_SHAPES:
                self._process_node(item)
            elif item_type and (item_type.startswith('prov:') or item_type.startswith('provext:')):
                self._process_relation(item)
        
        return self._generate_dot()
    
    def _extract_namespaces(self, context: List[Any]) -> None:
        for ctx in context:
            if isinstance(ctx, dict):
                self.namespaces.update(ctx)
    
    def _shorten_uri(self, uri: str) -> str:
        if not uri or ':' not in uri:
            return uri
        if not uri.startswith('http://') and not uri.startswith('https://'):
            return uri
        for prefix, namespace in self.namespaces.items():
            if isinstance(namespace, str) and uri.startswith(namespace):
                return f"{prefix}:{uri[len(namespace):]}"
        
        return uri
    
    def _get_label(self, item: Dict[str, Any]) -> str:
        item_id = item.get('@id', '')
        
        # Check for prov:label
        if 'prov:label' in item:
            labels = item['prov:label']
            if labels and isinstance(labels, list) and len(labels) > 0:
                label_obj = labels[0]
                if isinstance(label_obj, dict) and '@value' in label_obj:
                    return label_obj['@value']
        
        # Check for other common label properties
        for label_prop in ['rdfs:label', 'foaf:name', 'dcterms:title', 'name', 'title']:
            if label_prop in item:
                values = item[label_prop]
                if values and isinstance(values, list) and len(values) > 0:
                    value_obj = values[0]
                    if isinstance(value_obj, dict) and '@value' in value_obj:
                        return value_obj['@value']
                    elif isinstance(value_obj, str):
                        return value_obj
        
        # Use ID as label
        if item_id:
            if ':' in item_id:
                return item_id.split(':', 1)[1]
            return item_id
        
        return 'anonymous'
    
    def _get_attributes_text(self, item: Dict[str, Any]) -> List[str]:
        attributes = []
        
        skip_props = {'@type', '@id', '@context', '@graph', 'prov:label', 'rdfs:label', 'foaf:name', 'dcterms:title'} | self.REFERENCE_PROPERTIES
        
        for key, value in item.items():
            if key in skip_props:
                continue
            
            short_key = self._shorten_uri(key) if ':' in key else key
            
            if isinstance(value, list) and len(value) > 0:
                for val_item in value[:3]:  # Show max 3 values
                    if isinstance(val_item, dict):
                        if '@value' in val_item:
                            val_str = str(val_item['@value'])
                            if len(val_str) > 30:
                                val_str = val_str[:27] + '...'
                            attributes.append(f"{short_key}={val_str}")
                    elif isinstance(val_item, str):
                        val_str = val_item
                        if len(val_str) > 30:
                            val_str = val_str[:27] + '...'
                        attributes.append(f"{short_key}={val_str}")
            elif isinstance(value, str):
                val_str = value
                if len(val_str) > 30:
                    val_str = val_str[:27] + '...'
                attributes.append(f"{short_key}={val_str}")
        
        return attributes
    
    def _process_node(self, item: Dict[str, Any]) -> None:
        item_type = item.get('@type')
        item_id = item.get('@id', f"anon_{len(self.nodes)}")
        
        label = self._get_label(item)
        
        if self.show_attributes:
            attributes = self._get_attributes_text(item)
            if attributes:
                # Limit to 5 attributes for readability
                attr_text = '\\n'.join(attributes[:5])
                label = f"{label}\\n{attr_text}"
        
        shape = self.NODE_SHAPES.get(item_type, 'ellipse')
        color = self.NODE_COLORS.get(item_type, '#FFFFFF')
        
        self.nodes[item_id] = {
            'label': label,
            'shape': shape,
            'fillcolor': color,
            'style': 'filled',
            'type': item_type
        }
    
    def _process_relation(self, item: Dict[str, Any]) -> None:
        self._process_simple_relation(item)
    
    def _has_attributes(self, item: Dict[str, Any]) -> bool:
        essential = {'@type', '@id'} | self.REFERENCE_PROPERTIES
        return any(key not in essential for key in item.keys())
    
    def _process_simple_relation(self, item: Dict[str, Any]) -> None:
        relation_type = item.get('@type')
        edge_style = self.EDGE_STYLES.get(relation_type, {})
        source, target = self._get_edge_endpoints(item, relation_type)
        if not source or not target:
            return
        
        edge = {
            'source': source,
            'target': target,
            'style': edge_style.get('style', 'solid'),
            'dir': edge_style.get('dir', 'forward'),
            'arrowhead': edge_style.get('arrowhead', 'normal')
        }

        if 'color' in edge_style:
            edge['color'] = edge_style['color']
        
        if self.show_relation_labels:
            label = edge_style.get('label', relation_type.split(':')[1])
            
            extra_info = []
            if 'prov:role' in item:
                roles = item['prov:role']
                if roles and isinstance(roles, list):
                    role_val = roles[0]
                    if isinstance(role_val, dict) and '@value' in role_val:
                        extra_info.append(f"role:{role_val['@value']}")
            
            if 'time' in item or 'prov:time' in item:
                time_val = item.get('time', item.get('prov:time'))
                if isinstance(time_val, str):
                    # Show just time portion for readability
                    if 'T' in time_val:
                        time_part = time_val.split('T')[1].split('.')[0]
                        extra_info.append(f"@{time_part}")
            
            if extra_info:
                label = f"{label}\\n({', '.join(extra_info)})"
            
            edge['label'] = label
        
        self.edges.append(edge)
    
    def _get_edge_endpoints(self, item: Dict[str, Any], relation_type: str) -> Tuple[Optional[str], Optional[str]]:
        if relation_type == 'prov:Generation':
            return item.get('activity'), item.get('entity')
        elif relation_type == 'prov:Usage':
            return item.get('activity'), item.get('entity')
        elif relation_type == 'prov:Derivation':
            return item.get('usedEntity'), item.get('generatedEntity')
        elif relation_type == 'prov:Association':
            return item.get('activity'), item.get('agent')
        elif relation_type == 'prov:Attribution':
            return item.get('entity'), item.get('agent')
        elif relation_type == 'prov:Communication':
            return item.get('informant'), item.get('informed')
        elif relation_type == 'prov:Delegation':
            return item.get('responsible'), item.get('delegate')
        elif relation_type == 'prov:Start':
            return item.get('trigger'), item.get('activity')
        elif relation_type == 'prov:End':
            return item.get('trigger'), item.get('activity')
        elif relation_type == 'prov:Invalidation':
            return item.get('activity'), item.get('entity')
        elif relation_type == 'prov:Influence':
            return item.get('influencer'), item.get('influencee')
        elif relation_type == 'provext:Specialization':
            return item.get('generalEntity'), item.get('specificEntity')
        elif relation_type == 'provext:Alternate':
            return item.get('alternate1'), item.get('alternate2')
        elif relation_type == 'provext:Membership':
            return item.get('collection'), item.get('entity')
        
        return None, None
    
    def _create_relation_edges(self, item: Dict[str, Any], relation_id: str, relation_type: str) -> None:
        for key, value in item.items():
            if key in self.REFERENCE_PROPERTIES and value:
                self.edges.append({
                    'source': relation_id,
                    'target': value,
                    'style': 'dotted',
                    'label': key,
                    'dir': 'forward'
                })
    
    def _generate_dot(self) -> str:
        lines = []
        
        lines.append('digraph PROV {')
        lines.append(f'  rankdir={self.direction};')
        lines.append('  node [fontname="Helvetica"];')
        lines.append('  edge [fontname="Helvetica"];')
        lines.append('')
        
        for node_id, node_props in self.nodes.items():
            props = [f'{k}="{v}"' for k, v in node_props.items()]
            props_str = ', '.join(props)
            safe_id = self._make_safe_id(node_id)
            lines.append(f'  {safe_id} [{props_str}];')
        
        lines.append('')
        
        for edge in self.edges:
            source = self._make_safe_id(edge['source'])
            target = self._make_safe_id(edge['target'])
            
            props = []
            if 'label' in edge and edge['label']:
                props.append(f'label="{edge["label"]}"')
            if 'style' in edge:
                props.append(f'style={edge["style"]}')
            if 'dir' in edge:
                props.append(f'dir={edge["dir"]}')
            if 'color' in edge:
                props.append(f'color="{edge["color"]}"')
            if 'arrowhead' in edge:
                props.append(f'arrowhead={edge["arrowhead"]}')
            
            props_str = ', '.join(props)
            if props_str:
                lines.append(f'  {source} -> {target} [{props_str}];')
            else:
                lines.append(f'  {source} -> {target};')
        
        lines.append('}')
        
        return '\n'.join(lines)
    
    def _make_safe_id(self, node_id: str) -> str:
        safe_id = node_id.replace(':', '_').replace('/', '_').replace('-', '_')
        safe_id = safe_id.replace('.', '_').replace('#', '_')
        
        if not safe_id.replace('_', '').isalnum():
            safe_id = f'"{node_id}"'
        
        return safe_id


def main():    
    parser = argparse.ArgumentParser(
        description='Convert PROV-JSONLD to Graphviz DOT format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument('input', type=str, required=True, help='Input PROV-JSONLD file (or stdin)')
    parser.add_argument('output', type=str, required=True, help='Output DOT file (or stdout)')
    parser.add_argument('--show-attr', type=bool, default=False, help='If attributes are shown or not')
    parser.add_argument('--render', type=str, default="png", choices=['png', 'pdf', 'svg'], help='Automatically render to image format (requires graphviz)')
    
    args = parser.parse_args()
    
    if args.input and args.input != '-':
        with open(args.input, 'r', encoding='utf-8') as f:
            prov_jsonld = json.load(f)
    else:
        prov_jsonld = json.load(sys.stdin)
    
    converter = ProvJsonldToGraphviz(show_attributes=True, direction="LR")
    dot_output = converter.convert(prov_jsonld)
    
    output_file = args.output
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(dot_output)
    print(f"Generated DOT file: {output_file}", file=sys.stderr)
    
    if args.render:
        output_image = output_file.rsplit('.', 1)[0] + f'.{args.render}'
        try:
            subprocess.run(['dot', f'-T{args.render}', output_file, '-o', output_image], check=True)
            print(f"Rendered image: {output_image}", file=sys.stderr)
        except FileNotFoundError:
            print("Warning: graphviz 'dot' command not found. Install graphviz to use --render", file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Error rendering: {e}", file=sys.stderr)

if __name__ == '__main__':
    main()
