import React, { useCallback, useMemo, useState, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Connection,
  NodeChange,
  EdgeChange,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  Panel,
  NodeTypes,
  MarkerType,
} from 'reactflow';
import { AlertTriangle, Maximize2, Download } from 'lucide-react';
import { SceneNode } from './SceneNode';
import { EndingNode } from './EndingNode';
import { NodePalette } from './NodePalette';
import { useCycleDetection } from './hooks/useCycleDetection';
import { useDagSync } from './hooks/useDagSync';
import type { ScriptNode, ScriptNodeCreate } from '@/services/scriptService';
import './DagEditor.css';

interface DagEditorProps {
  scriptId: string;
  initialNodes?: ScriptNode[];
  onNodesChange?: (nodes: ScriptNode[]) => void;
  onNodeSelect?: (node: ScriptNode) => void;
  onNodeCreate?: (node: ScriptNodeCreate) => Promise<ScriptNode>;
  onNodeUpdate?: (nodeId: string, data: Partial<ScriptNode>) => Promise<void>;
  onNodeDelete?: (nodeId: string) => Promise<void>;
  readOnly?: boolean;
}

const nodeTypes: NodeTypes = {
  scene: SceneNode,
  choice: SceneNode,
  ending: EndingNode,
};

const convertScriptNodeToFlowNode = (node: ScriptNode): Node => ({
  id: node.id,
  type: node.node_type || 'scene',
  position: { x: node.position_x || 0, y: node.position_y || 0 },
  data: {
    ...node,
    label: node.title || 'Untitled',
  },
});

const convertFlowNodeToScriptNode = (node: Node): Partial<ScriptNode> => ({
  id: node.id,
  node_type: node.type as 'scene' | 'choice' | 'ending',
  position_x: Math.round(node.position.x),
  position_y: Math.round(node.position.y),
  title: node.data.label,
  ...node.data,
});

export const DagEditor: React.FC<DagEditorProps> = ({
  scriptId,
  initialNodes = [],
  onNodesChange,
  onNodeSelect,
  onNodeCreate,
  onNodeUpdate,
  onNodeDelete,
  readOnly = false,
}) => {
  const initialFlowNodes = useMemo(() => 
    initialNodes.map(convertScriptNodeToFlowNode), 
    [initialNodes]
  );
  
  const initialEdges = useMemo(() => {
    const edges: Edge[] = [];
    initialNodes.forEach(node => {
      const choices = node.choices || [];
      choices.forEach((choice, index) => {
        if (choice.next_node_id) {
          edges.push({
            id: `${node.id}-${choice.next_node_id}`,
            source: node.id,
            target: choice.next_node_id,
            label: choice.text,
            markerEnd: { type: MarkerType.ArrowClosed },
            data: { choice },
          });
        }
      });
    });
    return edges;
  }, [initialNodes]);

  const [nodes, setNodes, onNodesChangeBase] = useNodesState(initialFlowNodes);
  const [edges, setEdges, onEdgesChangeBase] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  
  const { hasCycle } = useCycleDetection(nodes, edges);
  const { isLoading } = useDagSync(scriptId);

  const onNodesChangeHandler = useCallback(
    async (changes: NodeChange[]) => {
      if (readOnly) return;
      
      onNodesChangeBase(changes);
      
      for (const change of changes) {
        if (change.type === 'position' && change.position && onNodeUpdate) {
          await onNodeUpdate(change.id, {
            position_x: Math.round(change.position.x),
            position_y: Math.round(change.position.y),
          });
        }
      }
    },
    [readOnly, onNodesChangeBase, onNodeUpdate]
  );

  const onEdgesChangeHandler = useCallback(
    async (changes: EdgeChange[]) => {
      if (readOnly) return;
      onEdgesChangeBase(changes);
    },
    [readOnly, onEdgesChangeBase]
  );

  const onConnect = useCallback(
    async (connection: Connection) => {
      if (readOnly) return;
      if (!connection.source || !connection.target) return;
      const source = connection.source;
      const target = connection.target;
      
      const newEdge: Edge = {
        id: `${source}-${target}`,
        source,
        target,
        sourceHandle: connection.sourceHandle,
        targetHandle: connection.targetHandle,
        markerEnd: { type: MarkerType.ArrowClosed },
      };
      
      setEdges((eds) => addEdge(newEdge, eds));
      
      if (onNodeUpdate) {
        const sourceNode = nodes.find(n => n.id === source);
        if (sourceNode) {
          const currentChoices = ((sourceNode.data as { choices?: ScriptNode['choices'] }).choices) || [];
          await onNodeUpdate(source, {
            choices: [
              ...currentChoices,
              { id: `choice_${Date.now()}`, text: 'New Choice', next_node_id: target }
            ]
          });
        }
      }
    },
    [readOnly, setEdges, nodes, onNodeUpdate]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNode(node.id);
      if (onNodeSelect) {
        const scriptNode = convertFlowNodeToScriptNode(node) as ScriptNode;
        onNodeSelect(scriptNode);
      }
    },
    [onNodeSelect]
  );

  const onNodeDragStop = useCallback(
    async (_: React.MouseEvent, node: Node) => {
      if (readOnly || !onNodeUpdate) return;
      
      await onNodeUpdate(node.id, {
        position_x: Math.round(node.position.x),
        position_y: Math.round(node.position.y),
      });
    },
    [readOnly, onNodeUpdate]
  );

  const onDrop = useCallback(
    async (event: React.DragEvent) => {
      if (readOnly || !onNodeCreate) return;

      event.preventDefault();
      const type = event.dataTransfer.getData('application/reactflow');
      
      if (!type) return;

      const reactFlowBounds = event.currentTarget.getBoundingClientRect();
      const position = {
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      };

      const newNode: ScriptNodeCreate = {
        script_id: scriptId,
        node_type: type as 'scene' | 'choice' | 'ending',
        title: `New ${type}`,
        position_x: Math.round(position.x),
        position_y: Math.round(position.y),
      };

      const createdNode = await onNodeCreate(newNode);
      setNodes((nds) => [...nds, convertScriptNodeToFlowNode(createdNode)]);
    },
    [readOnly, scriptId, onNodeCreate, setNodes]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const handleFitView = useCallback(() => {
    const reactFlowInstance = document.querySelector('.react-flow') as HTMLElement;
    if (reactFlowInstance) {
      reactFlowInstance.dispatchEvent(new CustomEvent('fitView'));
    }
  }, []);

  const handleExportImage = useCallback(async () => {
    const flowElement = document.querySelector('.react-flow') as HTMLElement;
    if (!flowElement) return;

    try {
      const html2canvas = (await import('html2canvas')).default;
      const canvas = await html2canvas(flowElement, {
        backgroundColor: '#18181b',
        scale: 2,
      });
      
      const link = document.createElement('a');
      link.download = `script-${scriptId}-dag.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (error) {
      console.error('Failed to export image:', error);
    }
  }, [scriptId]);

  useEffect(() => {
    if (onNodesChange) {
      const scriptNodes = nodes.map(convertFlowNodeToScriptNode) as ScriptNode[];
      onNodesChange(scriptNodes);
    }
  }, [nodes, onNodesChange]);

  return (
    <div className="dag-editor" style={{ height: '100%', width: '100%' }}>
      {hasCycle && (
        <div className="cycle-warning">
          <AlertTriangle size={16} />
          Warning: Cycle detected! The story may loop infinitely.
        </div>
      )}
      
      {!readOnly && <NodePalette />}
      
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChangeHandler}
        onEdgesChange={onEdgesChangeHandler}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onNodeDragStop={onNodeDragStop}
        onDrop={onDrop}
        onDragOver={onDragOver}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
        nodesDraggable={!readOnly}
        nodesConnectable={!readOnly}
        elementsSelectable={!readOnly}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#3f3f46" />
        <Controls />
        <MiniMap 
          nodeColor={(node) => {
            switch (node.type) {
              case 'ending': return '#166534';
              case 'choice': return '#155e75';
              default: return '#312e81';
            }
          }}
          style={{ background: '#18181b' }}
        />
        
        <Panel position="top-right" className="flex gap-2">
          <button
          onClick={handleFitView}
          className="p-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-zinc-400 hover:text-white"
          title="Fit View"
          disabled={isLoading}
        >
            <Maximize2 size={16} />
          </button>
          <button
            onClick={handleExportImage}
            className="p-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-zinc-400 hover:text-white"
            title="Export as Image"
            disabled={isLoading}
          >
            <Download size={16} />
          </button>
        </Panel>
      </ReactFlow>
    </div>
  );
};

export default DagEditor;
