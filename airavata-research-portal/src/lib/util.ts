import { Resource } from "@/interfaces/ResourceType.ts";
import { ProjectType } from "@/interfaces/ProjectType.tsx";
import { StatusEnum } from "@/interfaces/StatusEnum";

export const resourceTypeToColor = (type: string) => {
  if (type === "NOTEBOOK") {
    return "blue";
  } else if (type === "REPOSITORY") {
    return "red";
  } else if (type === "DATASET") {
    return "green";
  } else if (type === "MODEL") {
    return "purple";
  } else {
    return "gray";
  }
}

export const isValidImaage = (url: string) => {
  // should start with http or https 

  if (url.startsWith("http")) {
    return true;
  }
  return false
}

export const getGithubOwnerAndRepo = (url: string) => {
  const match = url.match(/github\.com\/([^/]+)\/([^/]+)/);
  if (match) {
    const owner = match[1];
    const repo = match[2].replace(/\.git$/, "");
    return { owner, repo };
  }
  return null;
}

export const isResourceOwner = (userEmail: string, resource: Resource) => {
  return resource.authors
    .map((author) => author.authorId.toLowerCase())
    .includes(userEmail);
}

export const isProjectOwner = (userEmail: string, project: ProjectType) => {
  return project.ownerId.toLowerCase() === userEmail.toLowerCase();
}

export const isAdmin = (userEmail: string) => {
  const adminEmails = import.meta.env.VITE_ADMIN_EMAILS?.split(",") || [];
  return adminEmails.map((email: string) => email.toLowerCase()).includes(userEmail.toLowerCase());
}

export const getStatusColor = (status: StatusEnum) => {
  switch (status) {
    case StatusEnum.VERIFIED:
      return "green";
    case StatusEnum.REJECTED:
      return "red";
    case StatusEnum.PENDING:
      return "yellow";
    case StatusEnum.NONE:
      return "gray";
    default:
      return "gray";
  }
}