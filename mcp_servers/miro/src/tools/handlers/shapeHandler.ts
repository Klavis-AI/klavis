import { MiroClient } from '../../client/miroClient.js';

export class ShapeHandler {
  constructor(private miroClient: MiroClient) {}

  async createShape(
    boardId: string,
    data: {
      content?: string;
      shape?:
        | 'rectangle'
        | 'round_rectangle'
        | 'circle'
        | 'triangle'
        | 'rhombus'
        | 'parallelogram'
        | 'trapezoid'
        | 'pentagon'
        | 'hexagon'
        | 'octagon'
        | 'wedge_round_rectangle_callout'
        | 'star'
        | 'flow_chart_predefined_process'
        | 'cloud'
        | 'cross'
        | 'can'
        | 'right_arrow'
        | 'left_arrow'
        | 'left_right_arrow'
        | 'left_brace'
        | 'right_brace';
      borderColor?: string;
      borderOpacity?: number;
      borderStyle?: 'normal' | 'dotted' | 'dashed';
      borderWidth?: number;
      color?: string;
      fillColor?: string;
      fillOpacity?: number;
      fontFamily?: string;
      fontSize?: number;
      textAlign?: 'left' | 'center' | 'right';
      textAlignVertical?: 'top' | 'middle' | 'bottom';
      x?: number;
      y?: number;
      width?: number;
      height?: number;
      rotation?: number;
      parentId?: string;
    },
  ): Promise<any> {
    const payload: any = {
      data: {
        content: data.content || '',
        shape: data.shape || 'rectangle',
      },
      style: {
        borderColor: data.borderColor || '#1a1a1a',
        borderOpacity:
          data.borderOpacity !== undefined
            ? data.borderOpacity.toString()
            : data.borderColor
              ? '1.0'
              : '0.0',
        borderStyle: data.borderStyle || 'normal',
        borderWidth: data.borderWidth !== undefined ? data.borderWidth.toString() : '2.0',
        color: data.color || '#1a1a1a',
        fillColor: data.fillColor || '#ffffff',
        fillOpacity:
          data.fillOpacity !== undefined
            ? data.fillOpacity.toString()
            : data.fillColor
              ? '1.0'
              : '0.0',
        fontFamily: data.fontFamily || 'arial',
        fontSize: data.fontSize !== undefined ? data.fontSize.toString() : '14',
        textAlign: data.textAlign || 'center',
        textAlignVertical: data.textAlignVertical || 'top',
      },
    };

    if (data.x !== undefined || data.y !== undefined) {
      payload.position = {
        x: data.x || 0,
        y: data.y || 0,
      };
    }

    if (data.width || data.height || data.rotation !== undefined) {
      payload.geometry = {};
      if (data.width) payload.geometry.width = data.width;
      if (data.height) payload.geometry.height = data.height;
      if (data.rotation !== undefined) payload.geometry.rotation = data.rotation;
    }

    if (data.parentId) {
      payload.parent = {
        id: data.parentId,
      };
    }

    return this.miroClient.makeRequest(`/boards/${boardId}/shapes`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getShape(boardId: string, itemId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/shapes/${itemId}`, {
      method: 'GET',
    });
  }

  async updateShape(
    boardId: string,
    itemId: string,
    data: {
      content?: string;
      shape?:
        | 'rectangle'
        | 'round_rectangle'
        | 'circle'
        | 'triangle'
        | 'rhombus'
        | 'parallelogram'
        | 'trapezoid'
        | 'pentagon'
        | 'hexagon'
        | 'octagon'
        | 'wedge_round_rectangle_callout'
        | 'star'
        | 'flow_chart_predefined_process'
        | 'cloud'
        | 'cross'
        | 'can'
        | 'right_arrow'
        | 'left_arrow'
        | 'left_right_arrow'
        | 'left_brace'
        | 'right_brace';
      borderColor?: string;
      borderOpacity?: number;
      borderStyle?: 'normal' | 'dotted' | 'dashed';
      borderWidth?: number;
      color?: string;
      fillColor?: string;
      fillOpacity?: number;
      fontFamily?: string;
      fontSize?: number;
      textAlign?: 'left' | 'center' | 'right';
      textAlignVertical?: 'top' | 'middle' | 'bottom';
      x?: number;
      y?: number;
      width?: number;
      height?: number;
      rotation?: number;
      parentId?: string;
    },
  ): Promise<any> {
    const payload: any = {};

    if (data.content !== undefined || data.shape !== undefined) {
      payload.data = {};
      if (data.content !== undefined) payload.data.content = data.content;
      if (data.shape !== undefined) payload.data.shape = data.shape;
    }

    if (
      data.borderColor !== undefined ||
      data.borderOpacity !== undefined ||
      data.borderStyle !== undefined ||
      data.borderWidth !== undefined ||
      data.color !== undefined ||
      data.fillColor !== undefined ||
      data.fillOpacity !== undefined ||
      data.fontFamily !== undefined ||
      data.fontSize !== undefined ||
      data.textAlign !== undefined ||
      data.textAlignVertical !== undefined
    ) {
      payload.style = {};
      if (data.borderColor !== undefined) payload.style.borderColor = data.borderColor;
      if (data.borderOpacity !== undefined)
        payload.style.borderOpacity = data.borderOpacity.toString();
      if (data.borderStyle !== undefined) payload.style.borderStyle = data.borderStyle;
      if (data.borderWidth !== undefined) payload.style.borderWidth = data.borderWidth.toString();
      if (data.color !== undefined) payload.style.color = data.color;
      if (data.fillColor !== undefined) payload.style.fillColor = data.fillColor;
      if (data.fillOpacity !== undefined) payload.style.fillOpacity = data.fillOpacity.toString();
      if (data.fontFamily !== undefined) payload.style.fontFamily = data.fontFamily;
      if (data.fontSize !== undefined) payload.style.fontSize = data.fontSize.toString();
      if (data.textAlign !== undefined) payload.style.textAlign = data.textAlign;
      if (data.textAlignVertical !== undefined)
        payload.style.textAlignVertical = data.textAlignVertical;
    }

    if (data.x !== undefined || data.y !== undefined) {
      payload.position = {
        x: data.x,
        y: data.y,
      };
    }

    if (data.width || data.height || data.rotation !== undefined) {
      payload.geometry = {};
      if (data.width) payload.geometry.width = data.width;
      if (data.height) payload.geometry.height = data.height;
      if (data.rotation !== undefined) payload.geometry.rotation = data.rotation;
    }

    if (data.parentId !== undefined) {
      payload.parent = data.parentId ? { id: data.parentId } : null;
    }

    return this.miroClient.makeRequest(`/boards/${boardId}/shapes/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteShape(boardId: string, itemId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/shapes/${itemId}`, {
      method: 'DELETE',
    });
  }
}
