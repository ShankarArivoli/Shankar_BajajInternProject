import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from collections import defaultdict, deque

app = Flask(__name__)
CORS(app)

def process_graph_logic(data):
    valid_edges, invalid_entries, duplicate_edges = [], [], []
    seen_edges = set()
    edge_regex = re.compile(r'^[A-Z]->[A-Z]$')

    for entry in data:
        trimmed = str(entry).strip()
        if not edge_regex.match(trimmed) or trimmed[0] == trimmed[-2]:
            invalid_entries.append(entry)
            continue
        if trimmed in seen_edges:
            if trimmed not in duplicate_edges: duplicate_edges.append(trimmed)
            continue
        seen_edges.add(trimmed)
        valid_edges.append({'p': trimmed[0], 'c': trimmed[-1]})

    adj, in_degree, all_nodes, parents = defaultdict(list), defaultdict(int), set(), {}
    for e in valid_edges:
        all_nodes.update([e['p'], e['c']])
        if e['c'] not in parents:
            parents[e['c']] = e['p']
            adj[e['p']].append(e['c'])
            in_degree[e['c']] += 1
            if e['p'] not in in_degree: in_degree[e['p']] = 0

    visited_global, hierarchies = set(), []
    total_trees, total_cycles, max_depth, best_root = 0, 0, -1, ""

    for node in sorted(all_nodes):
        if node not in visited_global:
            comp, q = [], deque([node])
            visited_global.add(node)
            while q:
                u = q.popleft()
                comp.append(u)
                neighs = set(adj[u])
                for parent, children in adj.items():
                    if u in children: neighs.add(parent)
                for v in neighs:
                    if v not in visited_global and v in all_nodes:
                        visited_global.add(v)
                        q.append(v)
            
            roots = sorted([n for n in comp if in_degree[n] == 0])
            if not roots:
                total_cycles += 1
                hierarchies.append({"root": sorted(comp)[0], "tree": {}, "has_cycle": True})
            else:
                total_trees += 1
                root = roots[0]
                def get_tree(u): return {v: get_tree(v) for v in sorted(adj[u])}
                def get_depth(u): 
                    child_depths = [get_depth(v) for v in adj[u]]
                    return 1 + (max(child_depths) if child_depths else 0)
                
                depth = get_depth(root)
                hierarchies.append({"root": root, "tree": {root: get_tree(root)}, "depth": depth})
                if depth > max_depth or (depth == max_depth and (not best_root or root < best_root)):
                    max_depth, best_root = depth, root

    return hierarchies, invalid_entries, duplicate_edges, {"total_trees": total_trees, "total_cycles": total_cycles, "largest_tree_root": best_root}

@app.route('/bfhl', methods=['POST'])
def bfhl():
    try:
        req_json = request.get_json()
        if not req_json or 'data' not in req_json:
            return jsonify({"is_success": False, "message": "Missing 'data' field"}), 400
        data = req_json.get('data', [])
        h, inv, dup, summ = process_graph_logic(data)
        return jsonify({
            "user_id": "Shankar_P_A", "email_id": "sa3125@srmist.edu.in", "college_roll_number": "RA2311003020442",
            "hierarchies": h, "invalid_entries": inv, "duplicate_edges": dup, "summary": summ
        })
    except Exception as e:
        return jsonify({"is_success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
