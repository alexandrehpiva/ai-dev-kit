import { TextInput } from '@inkjs/ui';
import { Box, Text, useInput } from 'ink';
import React, { useState } from 'react';

export type TextPromptProps = {
  message: string;
  placeholder?: string;
  initialValue?: string;
  validate?: (value: string) => string | undefined;
  onDone: (value: string | 'cancel') => void;
};

export function TextPrompt({
  message,
  placeholder,
  initialValue,
  validate,
  onDone,
}: TextPromptProps): React.ReactElement {
  const [error, setError] = useState<string | null>(null);

  useInput((_input, key) => {
    if (key.escape) onDone('cancel');
  });

  return (
    <Box flexDirection="column" marginBottom={1}>
      <Text bold>{message}</Text>
      <Box marginTop={1}>
        <TextInput
          defaultValue={initialValue}
          placeholder={placeholder}
          onSubmit={(value) => {
            if (validate) {
              const err = validate(value);
              if (err !== undefined) {
                setError(err);
                return;
              }
            }
            setError(null);
            onDone(value);
          }}
        />
      </Box>
      {error ? (
        <Box marginTop={1}>
          <Text color="red">{error}</Text>
        </Box>
      ) : null}
      <Box marginTop={1}>
        <Text dimColor>enter confirm · esc cancel</Text>
      </Box>
    </Box>
  );
}
