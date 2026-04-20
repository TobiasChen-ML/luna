import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Flag, Star, Heart, Skull, Sparkles } from 'lucide-react';

interface EndingNodeData {
  label: string;
  title?: string;
  ending_type?: 'good' | 'neutral' | 'bad' | 'secret';
  description?: string;
}

const endingConfig = {
  good: {
    icon: Heart,
    color: 'text-green-400',
    bg: 'bg-green-500/20',
    label: 'Good Ending',
  },
  neutral: {
    icon: Flag,
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/20',
    label: 'Neutral Ending',
  },
  bad: {
    icon: Skull,
    color: 'text-red-400',
    bg: 'bg-red-500/20',
    label: 'Bad Ending',
  },
  secret: {
    icon: Sparkles,
    color: 'text-purple-400',
    bg: 'bg-purple-500/20',
    label: 'Secret Ending',
  },
};

export const EndingNode: React.FC<NodeProps<EndingNodeData>> = memo(({ data, selected }) => {
  const endingType = data.ending_type || 'neutral';
  const config = endingConfig[endingType] || endingConfig.neutral;
  const Icon = config.icon;

  return (
    <div className={`dag-node ending ${endingType} ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Top} />
      
      <div className="dag-node-header">
        <Icon size={14} className={config.color} />
        <span className={`dag-node-type ${config.bg} ${config.color}`}>
          {config.label}
        </span>
      </div>
      
      <div className="dag-node-title">{data.label || data.title || 'Ending'}</div>
      
      {data.description && (
        <div className="dag-node-description">
          {data.description.substring(0, 50)}
          {data.description.length > 50 ? '...' : ''}
        </div>
      )}
    </div>
  );
});

EndingNode.displayName = 'EndingNode';

export default EndingNode;
