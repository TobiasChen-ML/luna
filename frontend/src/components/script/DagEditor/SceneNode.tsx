import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { BookOpen, MessageSquare } from 'lucide-react';

interface SceneNodeData {
  label: string;
  title?: string;
  description?: string;
  node_type?: string;
  choices?: Array<{
    id: string;
    text: string;
    next_node_id?: string;
  }>;
}

export const SceneNode: React.FC<NodeProps<SceneNodeData>> = memo(({ data, selected }) => {
  return (
    <div className={`dag-node scene ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Top} />
      
      <div className="dag-node-header">
        <BookOpen size={14} className="text-indigo-400" />
        <span className="dag-node-type bg-indigo-500/30 text-indigo-300">Scene</span>
      </div>
      
      <div className="dag-node-title">{data.label || data.title || 'Scene'}</div>
      
      {data.description && (
        <div className="dag-node-description">
          {data.description.substring(0, 50)}
          {data.description.length > 50 ? '...' : ''}
        </div>
      )}
      
      {data.choices && data.choices.length > 0 && (
        <div className="dag-node-choices">
          {data.choices.slice(0, 3).map((choice, idx) => (
            <div key={choice.id || idx} className="dag-node-choice">
              {choice.text.substring(0, 30)}
              {choice.text.length > 30 ? '...' : ''}
            </div>
          ))}
          {data.choices.length > 3 && (
            <div className="dag-node-choice text-zinc-500">
              +{data.choices.length - 3} more
            </div>
          )}
        </div>
      )}
      
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
});

SceneNode.displayName = 'SceneNode';

export default SceneNode;
