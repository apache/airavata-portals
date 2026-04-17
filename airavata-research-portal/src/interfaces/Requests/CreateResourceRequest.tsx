import {PrivacyEnum} from "../PrivacyEnum";
import {ResourceAuthor} from "@/interfaces/ResourceAuthor.ts";

export interface CreateResourceRequest {
  name: string;
  description: string;
  tags: string[];
  headerImage: string;
  authors: ResourceAuthor[];
  privacy: PrivacyEnum;
}
