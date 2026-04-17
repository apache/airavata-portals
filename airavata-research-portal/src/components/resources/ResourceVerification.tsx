import { Resource } from "@/interfaces/ResourceType";
import { StatusEnum } from "@/interfaces/StatusEnum";
import { isResourceOwner } from "@/lib/util";
import { Badge } from "@chakra-ui/react";
import { MdOutlineVerifiedUser } from "react-icons/md";
import { useAuth } from "react-oidc-context";
import { Tooltip } from "../ui/tooltip";
import { RequestResourceVerification } from "./RequestResourceVerification";
import { toaster } from "../ui/toaster";

export const ResourceVerification = ({
  resource,
  setResource,
}: {
  resource: Resource;
  setResource: (resource: Resource) => void;
}) => {
  const auth = useAuth();
  const isAuthor = isResourceOwner(
    auth.user?.profile?.email || "INVALID",
    resource
  );

  return (
    <>
      {resource.status === StatusEnum.VERIFIED && (
        <Badge
          colorPalette="green"
          fontWeight="bold"
          px="2"
          py="1"
          borderRadius="md"
        >
          <MdOutlineVerifiedUser />
          Verified
        </Badge>
      )}

      {isAuthor && resource.status === StatusEnum.PENDING && (
        <Tooltip content="The pending status is only visible to this resource's authors. It indicates that the resource is pending verification by the Airavata team.">
          <Badge
            colorPalette="yellow"
            fontWeight="bold"
            px="2"
            py="1"
            borderRadius="md"
          >
            <MdOutlineVerifiedUser />
            Pending Verification
          </Badge>
        </Tooltip>
      )}

      {isAuthor && resource.status === StatusEnum.REJECTED && (
        <Tooltip content="The rejected status is only visible to this resource's authors. Please see below for details.">
          <RequestResourceVerification
            resource={resource}
            onRequestSubmitted={() => {
              setResource({
                ...resource,
                status: StatusEnum.PENDING,
              } as Resource);
              toaster.create({
                title: "Verification Requested",
                description:
                  "Your request for resource verification has been submitted.",
                type: "info",
              });
            }}
          />
        </Tooltip>
      )}

      {isAuthor && resource.status === StatusEnum.NONE && (
        <>
          <RequestResourceVerification
            resource={resource}
            onRequestSubmitted={() => {
              setResource({
                ...resource,
                status: StatusEnum.PENDING,
              } as Resource);
              toaster.create({
                title: "Verification Requested",
                description:
                  "Your request for resource verification has been submitted.",
                type: "info",
              });
            }}
          />
        </>
      )}
    </>
  );
};
