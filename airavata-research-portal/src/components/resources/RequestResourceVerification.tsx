import { Resource } from "@/interfaces/ResourceType";
import api from "@/lib/api";
import { CONTROLLER } from "@/lib/controller";
import { Button, Dialog, useDialog, CloseButton, Text } from "@chakra-ui/react";
import { useState } from "react";
import { MdOutlineVerifiedUser } from "react-icons/md";
import { StatusEnum } from "@/interfaces/StatusEnum";
import { IoMdClose } from "react-icons/io";

export const RequestResourceVerification = ({
  resource,
  onRequestSubmitted,
}: {
  resource: Resource;
  onRequestSubmitted?: () => void;
}) => {
  const [verificationRequestLoading, setVerificationRequestLoading] =
    useState(false);
  const dialog = useDialog();

  const onSubmitForVerification = async () => {
    console.log("Submitting resource for verification:", resource.id);
    setVerificationRequestLoading(true);
    await api.post(`${CONTROLLER.resources}/${resource.id}/verify`);
    setVerificationRequestLoading(false);
    dialog.setOpen(false);
    onRequestSubmitted?.();
  };

  return (
    <>
      <Dialog.RootProvider size="sm" value={dialog}>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.Header>
              <Dialog.Title>Resource Verification</Dialog.Title>
            </Dialog.Header>
            <Dialog.Body>
              {resource.status === StatusEnum.NONE && (
                <Text>
                  When you submit <b>{resource.name}</b> for verification, the
                  Airavata team will review it to ensure it meets the necessary
                  safety standards. This process may take some time, and you
                  will be notified once the verification is complete.
                </Text>
              )}

              {resource.status === StatusEnum.REJECTED && (
                <Text>
                  Unfortunately, we found issues with <b>{resource.name}</b>{" "}
                  that prevents it from being verified by our team. Please find
                  our comments on the resource details page. After you have made
                  those changes, you may re-submit this resource for
                  verification.
                </Text>
              )}
            </Dialog.Body>
            <Dialog.Footer>
              <Button
                width="100%"
                colorPalette="yellow"
                onClick={onSubmitForVerification}
              >
                Submit
              </Button>
            </Dialog.Footer>
            <Dialog.CloseTrigger asChild>
              <CloseButton size="sm" />
            </Dialog.CloseTrigger>
          </Dialog.Content>
        </Dialog.Positioner>
      </Dialog.RootProvider>

      {resource.status === StatusEnum.NONE && (
        <Button
          size="2xs"
          colorPalette={"yellow"}
          onClick={() => {
            dialog.setOpen(true);
          }}
          loading={verificationRequestLoading}
        >
          <MdOutlineVerifiedUser />
          Request Verification
        </Button>
      )}

      {resource.status === StatusEnum.REJECTED && (
        <Button
          size="2xs"
          colorPalette={"red"}
          onClick={() => {
            dialog.setOpen(true);
          }}
        >
          <IoMdClose />
          Verification Rejected
        </Button>
      )}
    </>
  );
};
