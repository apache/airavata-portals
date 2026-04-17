import { toaster } from "@/components/ui/toaster";
import { Resource } from "@/interfaces/ResourceType";
import { StatusEnum } from "@/interfaces/StatusEnum";
import api from "@/lib/api";
import { CONTROLLER } from "@/lib/controller";
import {
  Button,
  HStack,
  Dialog,
  useDialog,
  Text,
  Textarea,
  CloseButton,
} from "@chakra-ui/react";
import { useState } from "react";

export const VerificationControls = ({
  resource,
  setResource,
}: {
  resource: Resource;
  setResource: (resource: Resource) => void;
}) => {
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [rejectLoading, setRejectLoading] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const dialog = useDialog();

  if (!resource || resource.status !== StatusEnum.PENDING) {
    return null; // Only show controls for resources pending verification
  }

  const onSubmitVerify = async () => {
    try {
      setVerifyLoading(true);
      const response = await api.post(
        `${CONTROLLER.admin}/resources/${resource.id}/verify`
      );
      setResource(response.data);
    } catch {
      toaster.create({
        title: "Error verifying resource",
        type: "error",
      });
    } finally {
      setVerifyLoading(false);
    }
  };

  const onSubmitForVerification = async () => {
    if (!rejectReason.trim()) {
      toaster.create({
        title: "Rejection reason is required",
        type: "error",
      });
      return;
    }

    try {
      setRejectLoading(true);
      const response = await api.post(
        `${CONTROLLER.admin}/resources/${resource.id}/reject`,
        rejectReason
      );
      setResource(response.data);
      dialog.setOpen(false);
    } catch {
      toaster.create({
        title: "Error rejecting resource",
        type: "error",
      });
    } finally {
      setRejectLoading(false);
    }
  };

  return (
    <>
      <HStack gap={2} mt={4}>
        <Button
          size="xs"
          colorPalette="red"
          onClick={() => dialog.setOpen(true)}
        >
          Reject
        </Button>

        <Button
          size="xs"
          colorPalette="green"
          loading={verifyLoading}
          onClick={onSubmitVerify}
        >
          Verify
        </Button>
      </HStack>

      <Dialog.RootProvider size="sm" value={dialog}>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.Header>
              <Dialog.Title>Reject Resource</Dialog.Title>
            </Dialog.Header>
            <Dialog.Body>
              <Text>
                Please provide a reason for rejecting the resource{" "}
                <b>{resource.name}</b>.
              </Text>
              <Textarea
                mt={2}
                placeholder="Enter rejection reason"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                rows={4}
              />
            </Dialog.Body>
            <Dialog.Footer>
              <Button
                width="100%"
                colorPalette="red"
                onClick={onSubmitForVerification}
                loading={rejectLoading}
              >
                Reject
              </Button>
            </Dialog.Footer>
            <Dialog.CloseTrigger asChild>
              <CloseButton size="sm" />
            </Dialog.CloseTrigger>
          </Dialog.Content>
        </Dialog.Positioner>
      </Dialog.RootProvider>
    </>
  );
};
