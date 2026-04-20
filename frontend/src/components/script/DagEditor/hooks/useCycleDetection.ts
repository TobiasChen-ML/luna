import { useMemo } from 'react';
import type { Node, Edge } from 'reactflow';

interface CycleResult {
  hasCycle: boolean;
  cyclePath: string[];
}

export const useCycleDetection = (nodes: Node[], edges: Edge[]): CycleResult => {
  const result = useMemo(() => {
    if (nodes.length === 0 || edges.length === 0) {
      return { hasCycle: false, cyclePath: [] };
    }

    const adjacencyList = new Map<string, string[]>();
    
    nodes.forEach(node => {
      adjacencyList.set(node.id, []);
    });
    
    edges.forEach(edge => {
      const source = edge.source;
      const target = edge.target;
      if (adjacencyList.has(source)) {
        adjacencyList.get(source)!.push(target);
      }
    });

    const WHITE = 0;
    const GRAY = 1;
    const BLACK = 2;
    
    const color = new Map<string, number>();
    const parent = new Map<string, string | null>();
    let cycleStart: string | null = null;
    let cycleEnd: string | null = null;
    
    nodes.forEach(node => {
      color.set(node.id, WHITE);
      parent.set(node.id, null);
    });

    const dfs = (nodeId: string): boolean => {
      color.set(nodeId, GRAY);
      
      const neighbors = adjacencyList.get(nodeId) || [];
      for (const neighbor of neighbors) {
        if (color.get(neighbor) === GRAY) {
          cycleStart = neighbor;
          cycleEnd = nodeId;
          return true;
        }
        
        if (color.get(neighbor) === WHITE) {
          parent.set(neighbor, nodeId);
          if (dfs(neighbor)) {
            return true;
          }
        }
      }
      
      color.set(nodeId, BLACK);
      return false;
    };

    for (const node of nodes) {
      if (color.get(node.id) === WHITE) {
        if (dfs(node.id)) {
          break;
        }
      }
    }

    if (cycleStart === null || cycleEnd === null) {
      return { hasCycle: false, cyclePath: [] };
    }

    const cyclePath: string[] = [cycleStart];
    let current = cycleEnd;
    
    while (current !== cycleStart) {
      cyclePath.unshift(current);
      current = parent.get(current) || '';
      if (!current) break;
    }
    cyclePath.unshift(cycleStart);

    return { hasCycle: true, cyclePath };
  }, [nodes, edges]);

  return result;
};

export default useCycleDetection;
