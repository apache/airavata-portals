import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router';
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Input,
  Flex,
  Badge,
  Wrap,
  WrapItem,
  Container,
  Divider
} from '@chakra-ui/react';
import ItemCard from '../common/ItemCard';
import { adminApiService } from '../../lib/adminApi';

interface SearchItem {
  id: number;
  title: string;
  description: string;
  tags: string[];
  authors: string[];
  starCount: number;
  category: string;
  type: 'model' | 'dataset' | 'notebook' | 'repository' | 'compute' | 'storage';
}

const SearchResults: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
  const [searchResults, setSearchResults] = useState<SearchItem[]>([]);
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [loading, setLoading] = useState(false);

  const popularTags = [
    'medical', 'cybersecurity', 'finance', 'nlp', 'computer-vision', 
    'protein', 'bioinformatics', 'fraud', 'machine-learning', 
    'deep-learning', 'time-series', 'classification', 'healthcare'
  ];

  const filterOptions = [
    { key: 'models', label: 'Models', icon: '🤖' },
    { key: 'repositories', label: 'Repositories', icon: '📁' },
    { key: 'notebooks', label: 'Notebooks', icon: '📓' },
    { key: 'datasets', label: 'Datasets', icon: '📊' },
    { key: 'compute', label: 'Compute Resources', icon: '💻' },
    { key: 'storage', label: 'Storage Resources', icon: '💾' },
    { key: 'authors', label: 'Authors', icon: '👤' }
  ];

  useEffect(() => {
    const query = searchParams.get('q');
    if (query) {
      setSearchQuery(query);
      performSearch(query);
    }
  }, [searchParams]);

  const performSearch = async (query: string) => {
    setLoading(true);
    try {
      console.log('Starting search for:', query);
      
      const promises = [
        adminApiService.searchModels(query).catch(err => {
          console.error('Models search failed:', err);
          return [];
        }),
        adminApiService.searchDatasets(query).catch(err => {
          console.error('Datasets search failed:', err);
          return [];
        }),
        adminApiService.searchNotebooks(query).catch(err => {
          console.error('Notebooks search failed:', err);
          return [];
        }),
        adminApiService.searchRepositories(query).catch(err => {
          console.error('Repositories search failed:', err);
          return [];
        }),
        adminApiService.searchComputeResources(query).catch(err => {
          console.error('Compute resources search failed:', err);
          return [];
        }),
        adminApiService.searchStorageResources(query).catch(err => {
          console.error('Storage resources search failed:', err);
          return [];
        })
      ];

      const [models, datasets, notebooks, repositories, computeResources, storageResources] = await Promise.all(promises);

      console.log('Search results:', {
        models: models.length,
        datasets: datasets.length,
        notebooks: notebooks.length,
        repositories: repositories.length,
        computeResources: computeResources.length,
        storageResources: storageResources.length
      });

      const allResults: SearchItem[] = [
        ...models.map((item: any) => ({ ...item, type: 'model' as const })),
        ...datasets.map((item: any) => ({ ...item, type: 'dataset' as const })),
        ...notebooks.map((item: any) => ({ ...item, type: 'notebook' as const })),
        ...repositories.map((item: any) => ({ ...item, type: 'repository' as const })),
        ...computeResources.map((item: any) => ({ 
          ...item, 
          type: 'compute' as const,
          title: item.name,
          tags: [],
          authors: [],
          starCount: 0,
          category: item.computeType || 'general'
        })),
        ...storageResources.map((item: any) => ({ 
          ...item, 
          type: 'storage' as const,
          title: item.name,
          tags: [],
          authors: [],
          starCount: 0,
          category: item.storageType || 'general'
        }))
      ];

      setSearchResults(allResults);
      setTotalResults(allResults.length);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      performSearch(searchQuery);
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleTagClick = (tag: string) => {
    setSearchQuery(tag);
    performSearch(tag);
    navigate(`/search?q=${encodeURIComponent(tag)}`);
  };

  const handleFilterClick = (filterKey: string) => {
    if (selectedFilters.includes(filterKey)) {
      setSelectedFilters(selectedFilters.filter(f => f !== filterKey));
    } else {
      setSelectedFilters([...selectedFilters, filterKey]);
    }
  };

  const filteredResults = searchResults.filter(result => {
    if (selectedFilters.length === 0) return true;
    return selectedFilters.some(filter => {
      switch (filter) {
        case 'models':
          return result.type === 'model';
        case 'datasets':
          return result.type === 'dataset';
        case 'notebooks':
          return result.type === 'notebook';
        case 'repositories':
          return result.type === 'repository';
        default:
          return true;
      }
    });
  });

  const getResultsByType = (type: string) => {
    return filteredResults.filter(result => result.type === type);
  };

  const renderResultSection = (type: string, title: string, results: SearchItem[]) => {
    if (results.length === 0) return null;

    return (
      <Box mb={8}>
        <HStack mb={4} spacing={3}>
          <Text fontSize="lg" fontWeight="bold">
            {title} ({results.length})
          </Text>
          <Button variant="link" color="blue.500" fontSize="sm">
            View All
          </Button>
        </HStack>
        <VStack spacing={4} align="stretch">
          {results.slice(0, 3).map((item) => (
            <Box key={`${item.type}-${item.id}`} p={4} border="1px solid" borderColor="gray.200" borderRadius="md">
              <HStack justify="space-between">
                <VStack align="start" spacing={2} flex={1}>
                  <Text fontWeight="bold" fontSize="md">{item.title}</Text>
                  <Text fontSize="sm" color="gray.600" noOfLines={2}>
                    {item.description}
                  </Text>
                  <HStack spacing={2}>
                    <Text fontSize="xs" color="blue.500">Authors:</Text>
                    <Text fontSize="xs" color="gray.600">
                      {item.authors.join(' • ')}
                    </Text>
                  </HStack>
                </VStack>
                <Button variant="outline" size="sm">
                  →
                </Button>
              </HStack>
            </Box>
          ))}
        </VStack>
      </Box>
    );
  };

  return (
    <Container maxW="container.xl" py={6}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack spacing={4}>
          <Button variant="ghost" onClick={() => navigate(-1)}>
          ← Back
        </Button>
        </HStack>

        {/* Search Bar */}
        <HStack spacing={4}>
          <Input
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            size="md"
            flex={1}
          />
          <Button onClick={handleSearch} bg="gray.800" color="white" _hover={{ bg: "gray.700" }}>
            ×
          </Button>
        </HStack>

        {/* Filter Buttons */}
        <HStack spacing={4} wrap="wrap">
          <Text fontSize="sm" color="gray.600">Filter:</Text>
          {filterOptions.map((filter) => (
            <Button
              key={filter.key}
              size="sm"
              variant={selectedFilters.includes(filter.key) ? "solid" : "outline"}
              bg={selectedFilters.includes(filter.key) ? "gray.800" : "transparent"}
              color={selectedFilters.includes(filter.key) ? "white" : "gray.700"}
              leftIcon={<span>{filter.icon}</span>}
              onClick={() => handleFilterClick(filter.key)}
            >
              {filter.label}
            </Button>
          ))}
        </HStack>

        {/* Popular Tags Section */}
        {searchQuery === '' && (
          <Box>
            <Text fontSize="md" fontWeight="bold" mb={4}>
              Popular Tags
            </Text>
            <Wrap spacing={2}>
              {popularTags.map((tag, index) => (
                <WrapItem key={index}>
                  <Badge
                    px={3}
                    py={1}
                    bg="gray.100"
                    color="gray.700"
                    borderRadius="full"
                    cursor="pointer"
                    _hover={{ bg: "gray.200" }}
                    onClick={() => handleTagClick(tag)}
                  >
                    + {tag}
                  </Badge>
                </WrapItem>
              ))}
            </Wrap>
          </Box>
        )}

        {/* Results */}
        {searchQuery && (
          <>
            <Text fontSize="lg" color="gray.600">
              {totalResults} Results
            </Text>

            {renderResultSection('model', 'Models', getResultsByType('model'))}
            {renderResultSection('repository', 'Repositories', getResultsByType('repository'))}
            {renderResultSection('notebook', 'Notebooks', getResultsByType('notebook'))}
            {renderResultSection('dataset', 'Datasets', getResultsByType('dataset'))}

            {loading && (
              <Text textAlign="center" color="gray.500">
                Loading...
              </Text>
            )}

            {!loading && filteredResults.length === 0 && searchQuery && (
              <Text textAlign="center" color="gray.500">
                No results found for "{searchQuery}"
              </Text>
            )}
          </>
        )}
      </VStack>
    </Container>
  );
};

export default SearchResults;