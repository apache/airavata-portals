export interface ResourceAuthor {
  authorId: string;
  role: AuthorRoleEnum;
}

enum AuthorRoleEnum {
  PRIMARY,
  SECONDARY,
  TERTIARY,
  QUATERNARY,
  QUINARY
}
