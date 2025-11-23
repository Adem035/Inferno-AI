/**
 * Welcome screen component
 */

import React from 'react';
import { Box, Text } from 'ink';
import BigText from 'ink-big-text';
import Gradient from 'ink-gradient';

interface WelcomeProps {
    version?: string;
}

export const Welcome: React.FC<WelcomeProps> = ({ version = '1.0.0' }) => {
    return (
        <Box flexDirection="column" paddingY={1}>
            <Gradient name="passion">
                <BigText text="Inferno" font="block" />
            </Gradient>

            <Box marginTop={1}>
                <Text bold color="gray">
                    Production-Grade Security Scanner v{version}
                </Text>
            </Box>
        </Box>
    );
};
