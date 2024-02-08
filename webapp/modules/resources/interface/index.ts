export interface GetResourcesResponse {
  documents: Documents[];
}

export interface Documents {
  document_pk: any;
  document_type: string;
  name: string;
  author: string;
  last_update_date: Date;
  text?: string;
}

export interface RefreshDocumentPayload {
  datetime: string;
  document_pk: number;
  edition?: string | undefined;
}
