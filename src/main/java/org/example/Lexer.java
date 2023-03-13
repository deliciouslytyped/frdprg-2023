package org.example;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class Main {
    enum State {
        KEZDOALLAPOT, AZONOSITOBAN, AZONOSITO_VEGE, SZAMBAN, SZAM_VEGE, BR_KOMMBEN, BR_KOMM_VEGE, LPAREN_TALALT,
        PR_KOMMBEN, PR_KOMMBEN_2, PR_KOMM_VEGE, COLON_TALALT, COLEQ_TOKEN, LT_TALALT, LEQ_TOKEN, GL_TOKEN,
        G_TALALT, GEQ_TOKEN, HIBAKEZELO, TOVABBFEJL, STOP
    }

    enum Input {
        LETTER, DIGIT, LBR, RBR, LP, ASTERISK, RP, COLON, EQ, LT, GT, SPC, OTHER, END
    }

    public static void main(String[] args) throws IOException {
        var source = dumpInput();
        var tokens = lexInput2();
        System.out.println(tokens);
        assert String.join("", (String[]) tokens.toArray()).equals(source);
    }

    public static String dumpInput() throws IOException {
        String source = Files.readString(Path.of("test.dml"));
        for (char c : source.toCharArray()){
            System.out.print(c);
        }
        System.out.println("\n----------------");
        return source;
    }

    public static int transition(int state, char c){
        int[][] transition = {
                {2, 4, 6, 19, 8, 19, 19, 12, 19, 14, 17, 1, 19, 21},
                {2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3},
                {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                {5, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5},
                {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                {6, 6, 6, 7, 6, 6, 6, 6, 6, 6, 6, 6, 6, 19},
                {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                {20, 20, 20, 20, 20, 9, 20, 20, 20, 20, 20, 20, 20, 19},
                {9, 9, 9, 9, 9, 10, 9, 9, 9, 9, 9, 9, 9, 19},
                {9, 9, 9, 9, 9, 10, 11, 9, 9, 9, 9, 9, 9, 19},
                {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                {20, 20, 20, 20, 20, 20, 20, 20, 13, 20, 20, 20, 20, 19},
                {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                {20, 20, 20, 20, 20, 20, 20, 20, 15, 20, 16, 20, 20, 19},
                {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                {20, 20, 20, 20, 20, 20, 20, 20, 18, 20, 20, 20, 20, 19},
                {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1}
        };
        for (int i = 0; i < transition.length; i++){ // rewrite table to have zero-based entries
            for (int j = 0; j < transition[i].length; j++) {
                transition[i][j] -= 1;
            }
        }

        if (Character.isLetter(c)){
            state = transition[state][Input.LETTER.ordinal()];
        } else if (Character.isDigit(c)) {
            state = transition[state][Input.DIGIT.ordinal()];
        } else {
            state = switch (c) {
                case '{' -> transition[state][Input.LBR.ordinal()];
                case '}' -> transition[state][Input.RBR.ordinal()];
                case '(' -> transition[state][Input.LP.ordinal()];
                case ')' -> transition[state][Input.RP.ordinal()];
                case '*' -> transition[state][Input.ASTERISK.ordinal()];
                case ':' -> transition[state][Input.COLON.ordinal()];
                case '=' -> transition[state][Input.EQ.ordinal()];
                case '<' -> transition[state][Input.LT.ordinal()];
                case '>' -> transition[state][Input.GT.ordinal()];
                case ' ' -> transition[state][Input.SPC.ordinal()];
                case '$' -> transition[state][Input.END.ordinal()];
                default -> transition[state][Input.OTHER.ordinal()];
            };
        }
        return state;
    }

    public static List<String> lexInput2() throws IOException {
        String source = Files.readString(Path.of("test.dml"));

        int[] backup = {0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1};
        int[] read =   {1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0};

        int state = State.KEZDOALLAPOT.ordinal();
        int i = 0;
        List<String> tokens = new ArrayList(Arrays.asList(""));

        loop:
        while(state != State.STOP.ordinal()) {

            char c = source.charAt(i);
            System.out.println(State.values()[state].name());

            // őszintén nem teljesen értem hogy ez miért itt működik
            var end = tokens.size() - 1;
            var last = tokens.get(end);
            if (read[state] == 1) { // TODO this is wrong  && state != State.KEZDOALLAPOT.ordinal() && state != State.STOP.ordinal() 
                tokens.set(end, last + c);
            }

            state = transition(state, c);

            switch (State.values()[state]){
                case COLEQ_TOKEN, GEQ_TOKEN, GL_TOKEN, LEQ_TOKEN, BR_KOMM_VEGE, PR_KOMM_VEGE -> {
                    tokens.add("");
                }
                case AZONOSITO_VEGE, SZAM_VEGE -> { // Ez működik de szerintem nem jó (mj: pontosan ezek a visszalépősök)
                    end = tokens.size() - 1;
                    last = tokens.get(end);
                    tokens.set(end, last.substring(0, last.length() - 1 ));
                    tokens.add("");
                }
                case HIBAKEZELO -> {
                    System.out.println("Szintaktikai (lexikális) hiba.");
                    break loop;
                }
            }

            if (read[state] == 1) i++;
            if (backup[state] == 1) i--;
        }

        tokens.remove(tokens.size()-1); // TODO assert that thelast token is empty and that is is the end
        return tokens;
    }

}