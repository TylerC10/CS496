package com.example.tyler.androidhttp;

import android.content.SharedPreferences;
import net.openid.appauth.AuthState;
import net.openid.appauth.AuthorizationException;
import net.openid.appauth.AuthorizationResponse;
import android.os.Bundle;
import android.support.annotation.Nullable;
import android.support.v7.app.AppCompatActivity;
import net.openid.appauth.AuthorizationService;
import net.openid.appauth.TokenResponse;

public class AuthActivityComplete extends AppCompatActivity {   //Another class used to get the response or exception (lecture function)

    private static final String TAG = AuthActivityComplete.class.getSimpleName();
    private AuthorizationService completeAuthorizationService;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_auth_complete);
        //Log.d(TAG, "Successful to this point.");

        completeAuthorizationService = new AuthorizationService(this);
        //Uri redirectUri = getIntent().getData();
        AuthorizationResponse response = AuthorizationResponse.fromIntent(getIntent());
        AuthorizationException exception = AuthorizationException.fromIntent(getIntent());

        if (response != null){
            final AuthState authState = new AuthState(response, exception);
            completeAuthorizationService.performTokenRequest(response.createTokenExchangeRequest(),
                    new AuthorizationService.TokenResponseCallback(){
                        @Override
                        public void onTokenRequestCompleted(@Nullable TokenResponse tokenResponse, @Nullable AuthorizationException authorizationException){
                            authState.update(tokenResponse, authorizationException);
                            SharedPreferences authorizationPreferences = getSharedPreferences("auth", MODE_PRIVATE);
                            authorizationPreferences.edit().putString("stateJson", authState.jsonSerializeString()).apply();
                            finish();
                        }
                    });
        }
    }
}
