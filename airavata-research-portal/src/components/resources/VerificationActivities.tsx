import { Resource } from "@/interfaces/ResourceType";
import { ResourceVerificationActivity } from "@/interfaces/ResourceVerificationActivity";
import api from "@/lib/api";
import { CONTROLLER } from "@/lib/controller";
import { getStatusColor, isAdmin, isResourceOwner } from "@/lib/util";
import {
  Box,
  Flex,
  Heading,
  Table,
  Spinner,
  Text,
  Badge,
} from "@chakra-ui/react";
import { useEffect, useState } from "react";
import { IoEyeOffOutline } from "react-icons/io5";
import { useAuth } from "react-oidc-context";
import { toaster } from "../ui/toaster";
import { StatusEnum } from "@/interfaces/StatusEnum";

export const VerificationActivities = ({
  resource,
}: {
  resource: Resource;
}) => {
  const [activities, setActivities] = useState<ResourceVerificationActivity[]>(
    []
  );
  const [loading, setLoading] = useState(false);
  const auth = useAuth();
  const userEmail = auth.user?.profile?.email || "";

  if (!isResourceOwner(userEmail, resource) && !isAdmin(userEmail)) {
    return null;
  }

  useEffect(() => {
    async function getData() {
      try {
        setLoading(true);
        const response = await api.get(
          `${CONTROLLER.resources}/${resource.id}/verification-activities`
        );
        setActivities(response.data);
      } catch (error) {
        toaster.create({
          title: "Failed to load verification activities",
          description: "Please try again later.",
          type: "error",
        });
      } finally {
        setLoading(false);
      }
    }

    getData();
  }, [resource]);

  return (
    <Box bg="gray.100" p={4} rounded="md">
      <Flex alignItems="center" gap={2}>
        <Heading fontWeight="bold" size="xl">
          Verification Activities
        </Heading>
        <IoEyeOffOutline size={24} />
      </Flex>
      <Text fontSize="sm" color="gray.700">
        This section is only visible to this resource's authors and
        administrators.
      </Text>

      {loading && <Spinner />}

      <Table.Root>
        <Table.Caption>
          Total {activities.length} verification activities
        </Table.Caption>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>Initiating User</Table.ColumnHeader>
            <Table.ColumnHeader>Created At</Table.ColumnHeader>
            <Table.ColumnHeader>Verification Status</Table.ColumnHeader>
            <Table.ColumnHeader>Comments</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>

        <Table.Body>
          {activities.map((activity: ResourceVerificationActivity) => (
            <Table.Row key={activity.id}>
              <Table.Cell>{activity.userId}</Table.Cell>
              <Table.Cell>
                {new Date(activity.createdAt).toLocaleString()}
              </Table.Cell>
              <Table.Cell>
                <Badge
                  colorPalette={getStatusColor(activity.status as StatusEnum)}
                >
                  {activity.status}
                </Badge>
              </Table.Cell>
              <Table.Cell>{activity.message}</Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Box>
  );
};
