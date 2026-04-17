import { ResourceCard } from "@/components/home/ResourceCard";
import { toaster } from "@/components/ui/toaster";
import { Resource } from "@/interfaces/ResourceType";
import api from "@/lib/api";
import { CONTROLLER } from "@/lib/controller";
import { Container, SimpleGrid, Spinner } from "@chakra-ui/react";
import { useEffect, useState } from "react";

export const PendingResourcesSection = () => {
  const [loading, setLoading] = useState(false);
  const [pendingResources, setPendingResources] = useState<Resource[]>([]);

  useEffect(() => {
    // Fetch pending resources from the API
    async function fetchPendingResources() {
      try {
        setLoading(true);
        const response = await api.get(`${CONTROLLER.admin}/resources/pending`);
        setPendingResources(response.data);
      } catch (error) {
        toaster.create({
          title: "Failed to load pending resources",
          description: "Please try again later.",
          type: "error",
        });
      } finally {
        setLoading(false);
      }
    }

    fetchPendingResources();
  }, []);

  return (
    <Container maxW="container.lg" mt={8}>
      {loading && <Spinner />}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={4} mt={4}>
        {pendingResources.map((resource) => (
          <ResourceCard key={resource.id} resource={resource} size="md" />
        ))}
      </SimpleGrid>
    </Container>
  );
};
