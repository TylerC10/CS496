package com.example.tyler.androidhttp;

import android.app.PendingIntent;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.support.annotation.Nullable;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.SimpleAdapter;
import android.widget.TextView;
import android.util.Log;
import android.view.View;
import net.openid.appauth.AuthState;
import net.openid.appauth.AuthorizationRequest;
import net.openid.appauth.AuthorizationService;
import net.openid.appauth.AuthorizationException;
import net.openid.appauth.AuthorizationServiceConfiguration;
import net.openid.appauth.ResponseTypeValues;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.io.IOException;
import java.util.Map;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import okhttp3.HttpUrl;



public class MainActivity extends AppCompatActivity {
    private AuthorizationService completeAuthorizationService;
    private AuthState authState;
    TextView access_token;
    private OkHttpClient client;
    private static final String TAG = MainActivity.class.getSimpleName();


    void requestAuthorization(){     //Request authorization. Code is from lecture
        Uri authEndPoint = new Uri.Builder().scheme("https").authority("accounts.google.com").path("o/oauth2/v2/auth").build();
        Uri tokenEndPoint = new Uri.Builder().scheme("https").authority("www.googleapis.com").path("/oauth2/v4/token").build();
        Uri redirect = new Uri.Builder().scheme("com.example.tyler.androidhttp").path("foo").build();

        AuthorizationServiceConfiguration config = new AuthorizationServiceConfiguration(authEndPoint, tokenEndPoint, null);
        AuthorizationRequest req = new AuthorizationRequest.Builder(config, "225923699401-hm2mfet400m5ahc3hki46qu9dmmoavp0.apps.googleusercontent.com", ResponseTypeValues.CODE, redirect)
                .setScopes("https://www.googleapis.com/auth/plus.me", "https://www.googleapis.com/auth/plus.stream.write", "https://www.googleapis.com/auth/plus.stream.read").build();
                //Build authorization and set the scopes. This is where we need to pass the Client ID we created on GAE
        Intent authComplete = new Intent(this, AuthActivityComplete.class);

        PendingIntent pendingIntent = PendingIntent.getActivity(this, req.hashCode(), authComplete, 0);
        completeAuthorizationService.performAuthorizationRequest(req, pendingIntent);
    }

    AuthState getOrCreateAuthState(){       //Function from lecture that is used to get hte auth state or create a new one if needed
        AuthState authorization = null;
        SharedPreferences authorizationPreference = getSharedPreferences("auth", MODE_PRIVATE);
        String stateJson = authorizationPreference.getString("stateJson", null);
        if(stateJson != null){
            try {
                authorization = AuthState.jsonDeserialize(stateJson);
            } catch (JSONException e){
                e.printStackTrace();
                return null;
            }
        }
        if (authorization != null && authorization.getAccessToken() != null){
            Log.d(TAG, authorization.getAccessToken());
            return authorization;
        } else {
            requestAuthorization();
            return null;
        }
    }

    public void requestAndResponse(){
        try {                           //This function will allow us to send Get requests. Strucutre is from lecture
            authState.performActionWithFreshTokens(completeAuthorizationService, new AuthState.AuthStateAction() {
                @Override
                public void execute(@Nullable String accessToken, @Nullable String idToken, @Nullable AuthorizationException authorizationException) {
                    if(authorizationException == null){
                        client = new OkHttpClient();    //Need the client from the library
                        HttpUrl url = HttpUrl.parse("https://www.googleapis.com/plusDomains/v1/people/me/activities/user"); //Parse the url
                        url = url.newBuilder().addQueryParameter("key", " AIzaSyARLf3S-hWDGFEhzntyFW9wcWfXd77lw_w").build(); //Add the parameters (the key is what was created in GAE)
                        url = url.newBuilder().addQueryParameter("maxResults", String.valueOf(3)).build(); //From assignment specs, we only want the last three posts

                        Request request = new Request.Builder() //Also from lecture, we now send the request
                                .url(url)
                                .addHeader("Authorization", "Bearer " + accessToken)  //Send the proper header (we are used to configuring headers from past API lessons and assignments)
                                .build();

                        client.newCall(request).enqueue(new Callback() {
                            @Override
                            public void onFailure(Call call, IOException e) {   //Standard error handling
                                Log.d(TAG, "Request Failes");
                                e.printStackTrace();
                            }
                            @Override
                            public void onResponse(Call call, Response response) throws IOException {
                                String resp = response.body().string(); //Save the response
                                try{
                                    //Log.d(TAG, response.toString());
                                    JSONObject jsonObject = new JSONObject(resp);       //Create a new JSON object
                                    JSONArray items = jsonObject.getJSONArray("items");
                                    List<Map<String,String>> posts = new ArrayList<Map<String,String>>();   //Build array list
                                    for(int i = 0; i < items.length(); i++){
                                        HashMap<String, String> m = new HashMap<String, String>();          //Get published and title
                                        m.put("published", items.getJSONObject(i).getString("published"));
                                        m.put("title",items.getJSONObject(i).getString("title"));
                                        posts.add(m);
                                    }

                                    final SimpleAdapter postAdapter = new SimpleAdapter(
                                            MainActivity.this,          //Simple adapter
                                            posts,
                                            R.layout.google_post_item,
                                            new String[]{"published", "title"},
                                            new int[]{R.id.first, R.id.second});

                                    runOnUiThread(new Runnable() {
                                        @Override
                                        public void run() {
                                            ((ListView) findViewById(R.id.postLists)).setAdapter(postAdapter); //Post the contents of list using adapter
                                        }
                                    });

                                } catch (JSONException e1){             //More error handling
                                    Log.d(TAG, response.toString());
                                    Log.d(TAG, "Response Failed");
                                    e1.printStackTrace();
                                }
                            }
                        });
                    }
                }
            });

        } catch(Exception e){
            e.printStackTrace();
        }
    }

    public void makePost(final String inputText) { //Function we'll use to send to our button when a user makes a new post
        try{
            authState.performActionWithFreshTokens(completeAuthorizationService, new AuthState.AuthStateAction(){
                @Override
                public void execute(@Nullable String accessToken, @Nullable String idToken, @Nullable AuthorizationException authorizationException){
                    if(authorizationException == null) {
                        client = new OkHttpClient();
                        String json = "{ 'object': { 'originalContent': '" +  inputText + "' }, 'access': { 'items':  [ { 'type': 'domain' } ], 'domainRestricted': true } }";
                        HttpUrl url = HttpUrl.parse("https://www.googleapis.com/plusDomains/v1/people/me/activities");
                        url = url.newBuilder().addQueryParameter("key", " AIzaSyARLf3S-hWDGFEhzntyFW9wcWfXd77lw_w").build();    //Build the URL
                        final MediaType mediaType = MediaType.parse("application/json; charset=utf-8");

                        RequestBody body = RequestBody.create(mediaType, json);
                        Request request = new Request.Builder()                     //Build the rest of the request
                                .url(url)
                                .post(body)
                                .addHeader("Authorization", "Bearer " + accessToken)
                                .build();

                        client.newCall(request).enqueue(new Callback() {        //Just like last function, call newCall and pass it the request we built
                            @Override
                            public void onFailure(Call call, IOException e) {
                                Log.d(TAG, "Request Failed");
                                e.printStackTrace();
                            }
                            @Override
                            public void onResponse(Call call, Response response) throws IOException {
                                String resp = response.body().string();
                                Log.d(TAG, response.toString());
                            }
                        });
                    }
                }
            });
        } catch (Exception pe){
            pe.printStackTrace();
        }
    }


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        completeAuthorizationService = new AuthorizationService(this);

        Button getPosts = (Button)findViewById(R.id.getPosts);      //Give button functionality to get the posts
        getPosts.setOnClickListener(new View.OnClickListener(){
            @Override
            public void onClick(View v) {
                requestAndResponse();
            }
        });


        Button googlePost = (Button) findViewById(R.id.sendPost);
        googlePost.setOnClickListener(new View.OnClickListener(){
            @Override
            public void onClick(View v) {
                EditText input_text = (EditText) findViewById(R.id.postInput); //Get the text the user sent, save it, and call the method to create posts
                final String newUserText = input_text.getText().toString();

                makePost(newUserText);
            }
        });
    }

    @Override
    protected void onStart(){
        authState = getOrCreateAuthState();     //Run this on start to check the AuthState
        super.onStart();
    }
}


