import { TRANSFORMERS, TextMatchTransformer } from "@lexical/markdown";
import { $createImageNode, $isImageNode, ImageNode } from "./imageNode";

export const IMAGE: TextMatchTransformer = {
    dependencies: [ImageNode],
    export: (node) => {
        if (!$isImageNode(node)) {
            return null;
        }

        return `![${node.getAltText()}](${node.getSrc()})`;
    },
    importRegExp: /!(?:\[([^[]*)\])(?:\(([^(]+)\))/,
    regExp: /!(?:\[([^[]*)\])(?:\(([^(]+)\))$/,
    replace: (textNode, match) => {
        const [, altText, src] = match;
        const imageNode = $createImageNode({
            altText,
            maxWidth: 800,
            src,
        });
        textNode.replace(imageNode);
    },
    trigger: ')',
    type: 'text-match',
};

import {
    ELEMENT_TRANSFORMERS,
    TEXT_FORMAT_TRANSFORMERS,
    TEXT_MATCH_TRANSFORMERS,
    Transformer,
} from '@lexical/markdown';

export const MOJODEX_LEXICAL_TRANSFORMERS: Array<Transformer> = [
    IMAGE,
    ...ELEMENT_TRANSFORMERS,
    ...TEXT_FORMAT_TRANSFORMERS,
    ...TEXT_MATCH_TRANSFORMERS,
]; // all built-in transformers + IMAGE special one