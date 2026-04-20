import { useCallback, useState } from 'react';
import { scriptService } from '@/services/scriptService';

export const useDagSync = (scriptId: string) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const syncNode = useCallback(async (nodeId: string, data: Partial<{
    position_x: number;
    position_y: number;
    title: string;
    choices: unknown[];
  }>) => {
    setIsLoading(true);
    setError(null);
    
    try {
      await scriptService.updateScript(scriptId, {
        nodes: [{ id: nodeId, ...data }]
      } as never);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sync failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [scriptId]);

  const syncEdge = useCallback(async (sourceId: string, targetId: string, choiceText?: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sync failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const validateDag = useCallback(async () => {
    try {
      const result = await scriptService.validateDAG(scriptId);
      return result.valid;
    } catch (err) {
      return false;
    }
  }, [scriptId]);

  return {
    syncNode,
    syncEdge,
    validateDag,
    isLoading,
    error,
  };
};

export default useDagSync;