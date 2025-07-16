import React, { useState, useEffect } from 'react';
import { initializeApp } from 'firebase/app';
import { getAuth, signInAnonymously, signInWithCustomToken } from 'firebase/auth';
import { getFirestore, doc, setDoc, getDoc } from 'firebase/firestore';

// Define the main App component
const App = () => {
    // State variables for Firebase and user authentication
    const [db, setDb] = useState(null);
    const [auth, setAuth] = useState(null);
    const [userId, setUserId] = useState(null);
    const [isAuthReady, setIsAuthReady] = useState(false);

    // Agent configuration states
    const [agentName, setAgentName] = useState('');
    const [agentRole, setAgentRole] = useState('');
    const [agentGoal, setAgentGoal] = useState('');
    const [agentTools, setAgentTools] = useState('');
    const [agentOutput, setAgentOutput] = useState('Agent output will appear here...');
    const [isLoading, setIsLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');

    // Initialize Firebase and set up authentication
    useEffect(() => {
        try {
            // Firebase configuration is provided globally by the Canvas environment
            const firebaseConfig = typeof __firebase_config !== 'undefined'
                ? JSON.parse(__firebase_config)
                : {};

            const app = initializeApp(firebaseConfig);
            const firestoreDb = getFirestore(app);
            const firebaseAuth = getAuth(app);

            setDb(firestoreDb);
            setAuth(firebaseAuth);

            // Sign in with custom token if available, otherwise anonymously
            const initialAuthToken = typeof __initial_auth_token !== 'undefined'
                ? __initial_auth_token
                : null;

            if (initialAuthToken) {
                signInWithCustomToken(firebaseAuth, initialAuthToken)
                    .then((userCredential) => {
                        setUserId(userCredential.user.uid);
                        setIsAuthReady(true);
                    })
                    .catch((error) => {
                        console.error('Error signing in with custom token:', error);
                        signInAnonymously(firebaseAuth)
                            .then((userCredential) => {
                                setUserId(userCredential.user.uid);
                                setIsAuthReady(true);
                            })
                            .catch((anonError) => {
                                console.error('Error signing in anonymously:', anonError);
                                setErrorMessage('Failed to authenticate with Firebase.');
                                setIsAuthReady(true); // Still set ready even if auth failed
                            });
                    });
            } else {
                signInAnonymously(firebaseAuth)
                    .then((userCredential) => {
                        setUserId(userCredential.user.uid);
                        setIsAuthReady(true);
                    })
                    .catch((error) => {
                        console.error('Error signing in anonymously:', error);
                        setErrorMessage('Failed to authenticate with Firebase.');
                        setIsAuthReady(true); // Still set ready even if auth failed
                    });
            }
        } catch (error) {
            console.error("Firebase initialization error:", error);
            setErrorMessage("Failed to initialize Firebase.");
            setIsAuthReady(true);
        }
    }, []);

    // Load agent configuration from Firestore when auth is ready
    useEffect(() => {
        if (isAuthReady && db && userId) {
            const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-app-id';
            const agentDocRef = doc(db, `artifacts/${appId}/users/${userId}/agentConfig`, 'currentAgent');

            const fetchAgentConfig = async () => {
                try {
                    const docSnap = await getDoc(agentDocRef);
                    if (docSnap.exists()) {
                        const data = docSnap.data();
                        setAgentName(data.name || '');
                        setAgentRole(data.role || '');
                        setAgentGoal(data.goal || '');
                        setAgentTools(data.tools || '');
                    }
                } catch (error) {
                    console.error("Error fetching agent config:", error);
                    setErrorMessage("Failed to load agent configuration.");
                }
            };
            fetchAgentConfig();
        }
    }, [isAuthReady, db, userId]);

    // Save agent configuration to Firestore
    const saveAgentConfig = async () => {
        if (!db || !userId) {
            setErrorMessage("Firebase not ready. Cannot save config.");
            return;
        }
        const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-app-id';
        const agentDocRef = doc(db, `artifacts/${appId}/users/${userId}/agentConfig`, 'currentAgent');
        try {
            await setDoc(agentDocRef, {
                name: agentName,
                role: agentRole,
                goal: agentGoal,
                tools: agentTools,
                timestamp: new Date()
            });
            console.log("Agent configuration saved!");
        } catch (error) {
            console.error("Error saving agent config:", error);
            setErrorMessage("Failed to save agent configuration.");
        }
    };

    // Handle agent run simulation
    const handleAgentRun = async () => {
        setAgentOutput('Agent is thinking...');
        setIsLoading(true);
        setErrorMessage('');

        const prompt = `
        You are an AI agent.
        Agent Name: ${agentName || 'Unnamed Agent'}
        Role: ${agentRole || 'General Assistant'}
        Goal: ${agentGoal || 'Provide helpful and concise information.'}
        Available Tools: ${agentTools || 'None'}

        Based on your role, goal, and available tools, describe your next action or thought process.
        `;

        try {
            let chatHistory = [];
            chatHistory.push({ role: "user", parts: [{ text: prompt }] });
            const payload = { contents: chatHistory };
            const apiKey = ""; // Canvas will automatically provide the API key

            const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`;

            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (result.candidates && result.candidates.length > 0 &&
                result.candidates[0].content && result.candidates[0].content.parts &&
                result.candidates[0].content.parts.length > 0) {
                const text = result.candidates[0].content.parts[0].text;
                setAgentOutput(text);
            } else {
                setAgentOutput('Error: Could not get a valid response from the agent.');
                console.error('Gemini API response structure unexpected:', result);
                setErrorMessage('Error: Invalid response from Gemini API.');
            }
        } catch (error) {
            console.error('Error running agent:', error);
            setAgentOutput('Error: Failed to communicate with the agent.');
            setErrorMessage('Error: Failed to connect to Gemini API. Check console for details.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-700 text-white font-sans flex flex-col items-center p-4 sm:p-6">
            <style>
                {`
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
                body { font-family: 'Inter', sans-serif; }
                `}
            </style>

            <div className="w-full max-w-4xl bg-gray-800 rounded-xl shadow-2xl p-6 sm:p-8 space-y-6">
                <h1 className="text-4xl font-bold text-center text-blue-400 mb-8">AI Agent Configurator</h1>

                {errorMessage && (
                    <div className="bg-red-600 text-white p-3 rounded-lg text-center font-medium">
                        {errorMessage}
                    </div>
                )}

                {userId && (
                    <div className="text-sm text-gray-400 text-center mb-4">
                        User ID: <span className="font-mono text-blue-300 break-all">{userId}</span>
                    </div>
                )}

                {/* Agent Configuration Section */}
                <div className="space-y-4">
                    <div className="flex flex-col">
                        <label htmlFor="agentName" className="text-gray-300 text-lg font-medium mb-1">Agent Name</label>
                        <input
                            type="text"
                            id="agentName"
                            className="p-3 rounded-lg bg-gray-700 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
