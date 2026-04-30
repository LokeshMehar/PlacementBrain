import { useQuery, useMutation, useQueryClient } from 'react-query';
import { getSources, deleteSource } from '../api/sources';

export function useSourcesList() {
  const { data, isLoading, refetch } = useQuery('sources', getSources, {
    refetchInterval: 30000, // Refresh every 30s
  });

  return {
    sources: data || [],
    isLoading,
    refetch,
  };
}

export function useDeleteSource() {
  const queryClient = useQueryClient();

  return useMutation(deleteSource, {
    onSuccess: () => {
      queryClient.invalidateQueries('sources');
    },
  });
}
