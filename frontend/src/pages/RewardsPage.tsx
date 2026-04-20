import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CommingSoonModal } from '@/components/common';

export function RewardsPage() {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(true);

  const handleClose = () => {
    setIsOpen(false);
    navigate(-1);
  };

  return <CommingSoonModal isOpen={isOpen} onClose={handleClose} />;
}

export default RewardsPage;
