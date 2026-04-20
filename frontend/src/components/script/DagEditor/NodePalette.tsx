import React from 'react';
import { BookOpen, GitBranch, Flag } from 'lucide-react';

const nodeTypes = [
  { type: 'scene', label: 'Scene', icon: BookOpen, description: 'Story scene node' },
  { type: 'choice', label: 'Choice', icon: GitBranch, description: 'Branching choice' },
  { type: 'ending', label: 'Ending', icon: Flag, description: 'Story ending' },
];

export const NodePalette: React.FC = () => {
  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="node-palette">
      {nodeTypes.map(({ type, label, icon: Icon, description }) => (
        <div
          key={type}
          className={`node-palette-item ${type}`}
          draggable
          onDragStart={(e) => onDragStart(e, type)}
          title={description}
        >
          <Icon size={14} />
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
};

export default NodePalette;
