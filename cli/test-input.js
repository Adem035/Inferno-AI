#!/usr/bin/env node
import React from 'react';
import { render, Box, Text } from 'ink';
import TextInput from 'ink-text-input';

const App = () => {
    const [value, setValue] = React.useState('');
    const [submitted, setSubmitted] = React.useState(false);

    if (submitted) {
        return <Text>You entered: {value}</Text>;
    }

    return (
        <Box>
            <Text>Type something: </Text>
            <TextInput
                value={value}
                onChange={setValue}
                onSubmit={() => setSubmitted(true)}
            />
        </Box>
    );
};

render(<App />);
