%AIProj
M=csvread('patients.csv',1,0);
X=M(1:100,1:4);                       
Y=logical(M(1:100,5)>=30);            % Classify training no-shows 
[b,~,stats] = glmfit(X,Y,'binomial'); % b are the coefficients