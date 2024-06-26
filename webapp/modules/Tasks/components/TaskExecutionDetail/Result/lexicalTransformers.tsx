import { $createImageNode, $isImageNode, ImageNode } from "./imageNode";
import { CODE, HEADING, QUOTE, TextMatchTransformer, UNORDERED_LIST } from "@lexical/markdown";
import {
    TEXT_FORMAT_TRANSFORMERS,
    TEXT_MATCH_TRANSFORMERS,
    Transformer,
} from '@lexical/markdown';

// This code is highly inspired by the code from the following link:
// https://github.com/facebook/lexical/blob/main/packages/lexical-playground/src/nodes/ImageNode.tsx
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


export const MOJODEX_LEXICAL_TRANSFORMERS: Array<Transformer> = [
    IMAGE,
    UNORDERED_LIST,
    CODE,
    HEADING,
    QUOTE,
    ...TEXT_FORMAT_TRANSFORMERS,
    ...TEXT_MATCH_TRANSFORMERS,
]; // all built-in transformers 
// + IMAGE special one made for Mojodex
// - ORDERED_LIST because it does not display numbers at start of line which is not desired