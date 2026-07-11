import { ConfirmInput } from '@inkjs/ui';
import { Box, Text, useInput } from 'ink';
import React from 'react';

export type ConfirmPromptProps = {
  message: string;
  initialValue?: boolean;
  onDone: (value: boolean | 'cancel') => void;
};

export function ConfirmPrompt({
  message,
  initialValue = false,
  onDone,
}: ConfirmPromptProps): React.ReactElement {
  useInput((_input, key) => {
    if (key.escape) onDone('cancel');
  });

  return (
    <Box flexDirection="column" marginBottom={1}>
      <Text bold>{message}</Text>
      <Box>
        <Text dimColor>Confirm </Text>
        <ConfirmInput
          defaultChoice={initialValue ? 'confirm' : 'cancel'}
          onConfirm={() => onDone(true)}
          onCancel={() => onDone(false)}
        />
      </Box>
      <Text dimColor>y/n · esc cancel</Text>
    </Box>
  );
}
