module full_adder (
	input wire CLOCK_50,
	input wire A,
	input wire B,
	input wire Cin,
	output wire Cout,
	output wire S

);


		assign S = (A ^ B) ^ Cin; //Soma
		assign Cout = (A & B) | (A & Cin) | (B & Cin); //Carry
		
endmodule 